import boto3, os
from crhelper import CfnResource
from . import logger
from .config_importer import (
    stop_task,
    run_task,
    kc_finished_importing,
    get_timestamp_now,
    get_task,
    get_task_logs_location,
    taken_too_long
)

helper = CfnResource(json_logging=False, log_level='INFO', boto_level='CRITICAL')

try:
    # Place initialization code here
    logs_client = boto3.client('logs')
    ecs_client = boto3.client('ecs')
    logger.info("Container initialization completed")
except Exception as e:
    helper.init_failure(e)

@helper.create
@helper.update
def create_update(event, context):
    logger.info(f"{event['RequestType']} request processing")
    cluster = event['ResourceProperties']['Cluster']
    task_definition = event['ResourceProperties']['TaskDefinition']
    task_subnets = event['ResourceProperties']['TaskSubnets']
    start_time = get_timestamp_now()
    task = run_task(ecs_client, cluster, task_subnets, task_definition)
    log_group, log_stream = get_task_logs_location(ecs_client, task_definition, task['taskArn'])
    helper.Data.update({
        'LogGroup': log_group,
        'LogStream': log_stream, 
        'TaskStartTime': start_time,
        'TaskArn': task['taskArn']
    })

@helper.poll_create
@helper.poll_update
def poll_create_update(event, context):
    # Return a resource id or True to indicate that creation is complete.
    logger.info(f"Polling {event['RequestType']} request processing")
    log_group = event['CrHelperData']['LogGroup']
    log_stream = event['CrHelperData']['LogStream']
    cluster = event['ResourceProperties']['Cluster']
    task_arn = event['CrHelperData']['TaskArn']
    start_time = event['CrHelperData']['TaskStartTime']
    task_status = get_task(ecs_client, cluster, task_arn)['lastStatus']
    task_timed_out = taken_too_long(start_time)
    if task_status  == 'STOPPED':
        raise RuntimeError(f"{task_arn} was found in unexpected stop state. Check {log_group}/{log_stream} for logs")
    # might be able to put a max runtime in task def and not need the task_timed_out check here
    elif task_status != 'RUNNING' and not task_timed_out:
        logger.info(f"{task_arn} status {task_status} not in stable state; checking again later")
        return
    if task_status == 'RUNNING' and not kc_finished_importing(logs_client, log_group, log_stream) and task_timed_out:
        stop_task(ecs_client, cluster, task_arn, "Import took longer than we want to wait")
        raise RuntimeError(f"KC Import config task ({task_arn}) still not done starting and we are done waiting")
    stop_task(ecs_client, cluster, task_arn, "Sucessfully imported config to kc")
    return f"{log_group}/{log_stream}"
    

@helper.delete
def delete(event, context):
    return event['PhysicalResourceId']

def handler(event, context):
    helper(event, context)