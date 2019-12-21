import boto3, os, logging, re
from crhelper import CfnResource
from datetime import datetime
from typing import List, Tuple

logger = logging.getLogger(__name__)
helper = CfnResource(json_logging=False, log_level='INFO', boto_level='CRITICAL')

try:
    # Place initialization code here
    logs_client = boto3.client('logs')
    ecs_client = boto3.client('ecs')
    logger.info("Container initialization completed")
except Exception as e:
    helper.init_failure(e)

def get_task_logs_location(task_definition: str, task_arn: str) -> Tuple[str,str]:
    task_definition = ecs_client.describe_task_definition(taskDefinition=task_arn)
    log_options = task_definition['taskDefinition']['containerDefinitions'][0]['logConfiguration']['options']
    task_id = task_arn.split('/')[-1]
    return (log_options['awslogs-group'], f"{log_options['awslogs-stream-prefix']}/{task_id}")

def run_task(cluster: str, task_subnets: List[str], task_definition: str) -> dict:
    # public ip is needed for fargate so that it can pull the container image.
    # if we set up a nat gateway/instance this can just be set to disabled either way.
    tasks = ecs_client.run_task(
        cluster              = cluster,
        launchType           = 'FARGATE',
        taskDefinition       = task_definition,
        count                = 1,
        networkConfiguration = {
            'awsvpcConfiguration' : {
                'subnets'       :  task_subnets,
                'assignPublicIp': 'ENABLED'
            }
        }
    )
    return tasks['tasks'][0]

def stop_task(cluster: str, task_arn: str, reason: str):
    ecs_client.stop_task(cluster=cluster, task=task_arn, reason=reason)

def get_timestamp_now() -> int:
    return int(datetime.utcnow().timestamp())

def kc_finished_starting(group: str, stream: str) -> bool:
    regex_match = r".*Keycloak \d\.\d\.\d \(WildFly Core \d+\.\d\.\d\.Final\) started"
    paginator = logs_client.get_paginator("filter_log_events")
    messages = []
    for logs in paginator.paginate(logGroupName=group, logStreamNames=[stream], filterPattern='started'):
        messages += [ event['message'] for event in logs['events'] if re.match(regex_match, event['message']) ]
    return len(messages) >= 3

def task_running(cluster: str, task_arn: str) -> bool:
    tasks = ecs_client.describe_tasks(cluster=cluster, tasks=[task_arn])['tasks']
    return tasks[0]['containers'][0]['lastStatus'] != 'STOPPED'

def taken_too_long(start_time: int) -> bool:
    ten_minutes = 600000
    return (get_timestamp_now() - start_time) > ten_minutes

@helper.create
@helper.update
def create_update(event, context):
    logger.info(f"{event['RequestType']} request processing")
    cluster = event['ResourceProperties']['Cluster']
    task_definition = event['ResourceProperties']['TaskDefinition']
    task_subnets = event['ResourceProperties']['TaskSubnets']
    start_time = get_timestamp_now()
    task = run_task(cluster, task_subnets, task_definition)
    log_group, log_stream = task_definition(task_definition, task['taskArn'])
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
    if not task_running(cluster, task_arn):
        raise RuntimeError(f"{task_arn} was found in unexpected stop state. Check {log_group}/{log_stream} for logs")
    if not kc_finished_starting(log_group, log_stream) and taken_too_long(start_time):
        stop_task(cluster, task_arn, "Import took longer than we want to wait")
        raise RuntimeError(f"KC Import config task ({task_arn}) still not done starting and we are done waiting")
    stop_task(cluster, task_arn, "Sucessfully imported config to kc")
    return f"{log_group}/{log_stream}"
    

@helper.delete
def delete(event, context):
    return event['PhysicalResourceId']

def handler(event, context):
    helper(event, context)