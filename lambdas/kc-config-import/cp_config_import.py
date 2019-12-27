import boto3, os
from . import logger
from .config_importer import (
    stop_task,
    run_task,
    kc_finished_starting,
    get_timestamp,
    get_task,
    get_task_logs_location,
    get_running_task,
    taken_too_long
)

logs_client = boto3.client('logs')
ecs_client = boto3.client('ecs')
logger.info("Container initialization completed")

# This really isn't doing anything useful at all.. but i wanted to explicitly give it a type
# since i'm considering having the generic cp invoke lambda helper consume the return value
class CodePipelineHelperResponse(object):
    def __init__(self, InProgress: bool, Success: bool = True, Message: str = ""):
        self.InProgress = InProgress
        self.Success = Success
        self.Message = Message

    def to_dict(self):
        return {
            'InProgress': self.InProgress,
            'Success': self.Success,
            'Message': self.Message
        }

def handler(event, context):
    cluster = os.environ['Cluster']
    task_definition = os.environ['TaskDefinition']
    task_family = os.environ['TaskFamily']
    task_subnets = os.environ['TaskSubnets'].split(',')
    running_task = get_running_task(ecs_client, cluster, task_family, task_definition)
    if not running_task:
        task = run_task(ecs_client, cluster, task_subnets, task_definition)
        return CodePipelineHelperResponse(**{'InProgress': True, 'Message': f'{task["taskArn"]} has been started'}).to_dict()
    start_time = get_timestamp(running_task['startedAt'])
    task_status = running_task['lastStatus']
    task_arn = running_task['taskArn']
    task_timed_out = taken_too_long(start_time)
    log_group, log_stream = get_task_logs_location(ecs_client, running_task['taskDefinitionArn'], task_arn)

    if task_status  == 'STOPPED':
        return CodePipelineHelperResponse(**{
            'InProgress': False, 
            'Success': False, 
            'Message': f"{task_arn} was found in unexpected stop state. Check {log_group}/{log_stream} for logs"
        }).to_dict()
    elif task_status != 'RUNNING' and not task_timed_out:
        return CodePipelineHelperResponse(**{
            'InProgress': True, 
            'Message': f"{task_arn} status {task_status} not in stable state; checking again later"
        }).to_dict()
    if task_status == 'RUNNING' and not kc_finished_starting(logs_client, log_group, log_stream) and task_timed_out:
        stop_task(ecs_client, cluster, task_arn, "Import took longer than we want to wait")
        return CodePipelineHelperResponse(**{
            'InProgress': False, 
            'Success': False, 
            'Message': f"KC Import config task ({task_arn}) still not done starting and we are done waiting"
        }).to_dict()
    stop_task(ecs_client, cluster, task_arn, "Sucessfully imported config to kc")
    return CodePipelineHelperResponse(**{
        'InProgress': False, 
        'Success': True, 
        'Message': f"{log_group}/{log_stream}"
    }).to_dict()