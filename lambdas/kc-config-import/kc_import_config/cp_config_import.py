import boto3, os
from . import logger
from .config_importer import (
    stop_task,
    run_task,
    kc_finished_starting,
    get_timestamp,
    get_timestamp_now,
    get_task,
    get_task_logs_location,
    find_task,
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
    task_subnets = os.environ['TaskSubnets'].split(',')
    logger.info(f"KC Config import lamba called with ImportId: {event['ImportId']}")
    # hashing and truncating to 35 chars to avoid hitting possible validation issues
    # might be worth a regex check and only hashing if it violates
    # > Up to 36 letters (uppercase and lowercase), numbers, hyphens, and underscores are allowed.
    import_id = str(hash(event['ImportId']))[-35:]
    task = find_task(ecs_client, cluster, import_id)
    if not task:
        logger.info(f"Unable to find previously started task with import id: {import_id} in cluster: {cluster}... starting one now")
        task = run_task(ecs_client, cluster, task_subnets, task_definition, import_id)
        logger.info(f"Started {task['taskArn']} in cluster {cluster}")
        return CodePipelineHelperResponse(**{'InProgress': True, 'Message': f'{task["taskArn"]} has been started'}).to_dict()
    
    task_status = task['lastStatus']
    task_arn = task['taskArn']
    logger.info(f"Found task {task_arn} previously started with import id {import_id} in cluster {cluster}")
    log_group, log_stream = get_task_logs_location(ecs_client, task['taskDefinitionArn'], task_arn)
    
    # Since this lambda is expecting to manage the running task 
    if task_status  == 'STOPPED':
        message = f"{task_arn} was found in unexpected stop state. Check {log_group}/{log_stream} for logs"
        logger.warning(message)
        return CodePipelineHelperResponse(**{
            'InProgress': False, 
            'Success': False, 
            'Message': message
        }).to_dict()
    elif task_status != 'RUNNING':
        message = f"{task_arn} status {task_status} not in stable state; checking again later"
        logger.info(message)
        return CodePipelineHelperResponse(**{
            'InProgress': True, 
            'Message': message
        }).to_dict()

    start_time =  get_timestamp(task['startedAt'])
    task_timed_out = taken_too_long(start_time)
    if not kc_finished_starting(logs_client, log_group, log_stream) and task_timed_out:
        message = f"KC Import config task ({task_arn}) still not done starting and we are done waiting"
        logger.warning(message)
        stop_task(ecs_client, cluster, task_arn, "Import took longer than we want to wait")
        return CodePipelineHelperResponse(**{
            'InProgress': False, 
            'Success': False, 
            'Message': message
        }).to_dict()
    logger.info(f"{task_arn} has successfully finished importing config; stopping it...")
    stop_task(ecs_client, cluster, task_arn, "Sucessfully imported config to kc")
    return CodePipelineHelperResponse(**{
        'InProgress': False, 
        'Success': True, 
        'Message': f"{log_group}/{log_stream}"
    }).to_dict()