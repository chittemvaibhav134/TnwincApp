import boto3, os, re
from typing import List, Tuple
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

SUCCESSFUL_STOP_REASON = "Successfully imported config to kc"
UNSUCCESSFUL_STOP_REASON = "Import took longer than we want to wait"

# This really isn't doing anything useful at all.. but i wanted to explicitly give it a type
# since i'm considering having the generic cp invoke lambda helper consume the return value
class CodePipelineHelperResponse(object):
    def __init__(self, InProgress: bool, Success: bool = True, Message: str = "", OutputVariables: dict = None):
        self.InProgress = InProgress
        self.Success = Success
        self.Message = Message
        self.OutputVariables = OutputVariables
    def to_dict(self):
        return {
            'InProgress': self.InProgress,
            'Success': self.Success,
            'Message': self.Message,
            'OutputVariables': self.OutputVariables
        }
    @classmethod
    def in_progress(cls, Message: str="") -> dict:
        return cls(True, True, Message).to_dict()
    @classmethod
    def failed(cls, Message: str) -> dict:
        return cls(False, False, Message).to_dict()
    @classmethod
    def succeeded(cls, Message: str="", OutputVariables: dict = None) -> dict:
        return cls(False, True, Message, OutputVariables).to_dict() 

def get_startedby_id(import_id: str):
    processed_id = import_id[-36:]
    # Constraint on ecs startedBy property:
    #   Up to 36 letters (uppercase and lowercase), numbers, hyphens, and underscores are allowed.
    regex = "^[a-zA-Z0-9_-]+$"
    if not re.search(regex, processed_id):
        logger.info(f"{import_id} violated regex filter; hashing id into something safe")
        processed_id = str(hash(processed_id))[-36:]
    logger.info(f"Import id {import_id} specified; using {processed_id} as startedBy id for task")
    return processed_id

def import_task_failed(task: dict) -> bool:
    return task['lastStatus']  == 'STOPPED' and task.get('stoppedReason') != SUCCESSFUL_STOP_REASON

def import_task_successfully_stopped(task: dict) -> bool:
    return task['lastStatus']  == 'STOPPED' and task.get('stoppedReason') == SUCCESSFUL_STOP_REASON

def import_task_still_starting_up(task: dict) -> bool:
    return task['lastStatus'] != 'RUNNING'

def import_task_timed_out(task: dict, log_group, log_stream) -> bool:
    task_timed_out = taken_too_long(get_timestamp(task['startedAt']))
    return not kc_finished_importing(logs_client, log_group, log_stream) and task_timed_out

def import_task_still_importing(task: dict, log_group, log_stream) -> bool:
    task_timed_out = taken_too_long(get_timestamp(task['startedAt']))
    return not kc_finished_importing(logs_client, log_group, log_stream) and not task_timed_out

def handler(event, context):
    cluster = os.environ['Cluster']
    task_definition = os.environ['TaskDefinition']
    task_subnets = os.environ['TaskSubnets'].split(',')
    import_config_container_name = os.environ['ImportConfigContainerName']
    logger.info(f"KC Config import lamba called with event: {event}")
    import_id = get_startedby_id(event['ImportId'])
    # Check if there is a running task with this import id already
    task = find_task(ecs_client, cluster, import_id)
    if not task:
        # kickoff import task if not
        logger.info(f"Unable to find previously started task with import id: {import_id} in cluster: {cluster}... starting one now")
        task = run_task(ecs_client, cluster, task_subnets, task_definition, import_id)
        message = f"Started {task['taskArn']} in cluster {cluster}"
        logger.info(message)
        return CodePipelineHelperResponse.in_progress(message)
    
    # if a task was found lets get more info from it to verify if it is 
    task_status = task['lastStatus']
    task_arn = task['taskArn']
    logger.info(f"Found task {task_arn} previously started with import id {import_id} in cluster {cluster}")
    log_group, log_stream = get_task_logs_location(ecs_client, task['taskDefinitionArn'], task_arn, import_config_container_name)
    
    if import_task_failed(task):
        message = f"{task_arn} was found in unexpected stop state. Check {log_group}/{log_stream} for logs"
        logger.warning(message)
        return CodePipelineHelperResponse.failed(message)
    elif import_task_successfully_stopped(task):
        message = f"{task_arn} was stopped after successful import. Returning success since this is most likely a retry that should no-op"
        logger.warning(message)
        return CodePipelineHelperResponse.succeeded(message)
    elif import_task_still_starting_up(task):
        message = f"{task_arn} status {task_status} not in stable state; check again later..."
        logger.info(message)
        return CodePipelineHelperResponse.in_progress(message)

    
    if import_task_still_importing(task, log_group, log_stream):
        message = f"KC Import config task ({task_arn}) still running through startup/import process; check again later..."
        logger.info(message)
        return CodePipelineHelperResponse.in_progress(message)
    elif import_task_timed_out(task, log_group, log_stream):
        message = f"KC Import config task ({task_arn}) still not done importing and we are done waiting"
        logger.warning(message)
        stop_task(ecs_client, cluster, task_arn, UNSUCCESSFUL_STOP_REASON)
        return CodePipelineHelperResponse.failed(message)

    # if here then the task is running as expected and has completed the import process
    # so it needs to get stopped
    message = f"{task_arn} has successfully finished importing config; stopping it..."
    logger.info(message)
    stop_task(ecs_client, cluster, task_arn, SUCCESSFUL_STOP_REASON )
    return CodePipelineHelperResponse.succeeded(message, OutputVariables={'TaskArn': task_arn})