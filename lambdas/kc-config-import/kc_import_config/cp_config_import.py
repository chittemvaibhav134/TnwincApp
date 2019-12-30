import boto3, os
from . import logger
from .config_importer import (
    stop_task,
    run_task,
    kc_finished_importing,
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
    @classmethod
    def in_progress(cls: CodePipelineHelperResponse, Message: str="") -> dict:
        return cls(True, True, Message).to_dict()
    @classmethod
    def failed(cls: CodePipelineHelperResponse, Message: str) -> dict:
        return cls(False, False, Message).to_dict()
    @classmethod
    def succeeded(cls: CodePipelineHelperResponse, Message: str="") -> dict:
        return cls(False, True, Message).to_dict() 

def handler(event, context):
    cluster = os.environ['Cluster']
    task_definition = os.environ['TaskDefinition']
    task_subnets = os.environ['TaskSubnets'].split(',')
    logger.info(f"KC Config import lamba called with event: {event}")
    
    # might be worth a regex check and only hashing if it violates
    # > Up to 36 letters (uppercase and lowercase), numbers, hyphens, and underscores are allowed.
    import_id = str(hash(event['ImportId']))[-35:]
    task = find_task(ecs_client, cluster, import_id)
    if not task:
        logger.info(f"Unable to find previously started task with import id: {import_id} in cluster: {cluster}... starting one now")
        task = run_task(ecs_client, cluster, task_subnets, task_definition, import_id)
        logger.info(f"Started {task['taskArn']} in cluster {cluster}")
        return CodePipelineHelperResponse.in_progress(f'{task["taskArn"]} has been started')
    
    task_status = task['lastStatus']
    task_arn = task['taskArn']
    logger.info(f"Found task {task_arn} previously started with import id {import_id} in cluster {cluster}")
    log_group, log_stream = get_task_logs_location(ecs_client, task['taskDefinitionArn'], task_arn)
    
    successful_stop_reason = "Successfully imported config to kc"

    if task_status  == 'STOPPED' and task.get('stoppedReason') != successful_stop_reason:
        message = f"{task_arn} was found in unexpected stop state. Check {log_group}/{log_stream} for logs"
        logger.warning(message)
        return CodePipelineHelperResponse.failed(message)
    elif task_status  == 'STOPPED' and task.get('stoppedReason') == successful_stop_reason:
        message = f"{task_arn} was stopped after successful import. Returning success since this is most likely a retry that should no-op"
        logger.warning(message)
        return CodePipelineHelperResponse.succeeded(message)
    elif task_status != 'RUNNING':
        message = f"{task_arn} status {task_status} not in stable state; checking again later"
        logger.info(message)
        return CodePipelineHelperResponse.in_progress(message)
    # since we know the task is RUNNING it should be safe to snag the startedAt prop now
    start_time =  get_timestamp(task['startedAt'])
    task_timed_out = taken_too_long(start_time)
    if not kc_finished_importing(logs_client, log_group, log_stream) and task_timed_out:
        message = f"KC Import config task ({task_arn}) still not done starting and we are done waiting"
        logger.warning(message)
        stop_task(ecs_client, cluster, task_arn, "Import took longer than we want to wait")
        return CodePipelineHelperResponse.failed(message)
    logger.info(f"{task_arn} has successfully finished importing config; stopping it...")
    stop_task(ecs_client, cluster, task_arn, successful_stop_reason )
    return CodePipelineHelperResponse.succeeded(message)