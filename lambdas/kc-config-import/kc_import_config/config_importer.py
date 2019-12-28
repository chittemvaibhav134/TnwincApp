import boto3, os, logging, re
from datetime import datetime
from typing import List, Tuple

logger = logging.getLogger(__name__)

def find_task(ecs_client, cluster, startedby_id):
    # check for running first because desiredStatus doesn't take mutliple values :/
    task_arns = ecs_client.list_tasks(cluster=cluster, desiredStatus='RUNNING', startedBy=startedby_id)['taskArns'] or ecs_client.list_tasks(cluster=cluster, desiredStatus='STOPPED', startedBy=startedby_id)['taskArns']
    if not task_arns:
        logger.info(f"No tasks found for cluster {cluster} with a startedBy of {startedby_id}")
        return
    if len(task_arns) > 1:
        logger.warn(f"Found {len(task_arns)} in {cluster} startedBy {startedby_id}.. there shouldn't be more than one and we are going to pretend there only was one")
    return ecs_client.describe_tasks(cluster=cluster, tasks=task_arns)['tasks'][0]

def get_task_logs_location(ecs_client, task_definition_arn: str, task_arn: str) -> Tuple[str,str]:
    task_definition = ecs_client.describe_task_definition(taskDefinition=task_definition_arn)
    log_options = task_definition['taskDefinition']['containerDefinitions'][0]['logConfiguration']['options']
    container_name = task_definition['taskDefinition']['containerDefinitions'][0]['name']
    task_id = task_arn.split('/')[-1]
    return (log_options['awslogs-group'], f"{log_options['awslogs-stream-prefix']}/{container_name}/{task_id}")

def run_task(ecs_client, cluster: str, task_subnets: List[str], task_definition: str, startedby_id: str = "config-importer") -> dict:
    # public ip is needed for fargate so that it can pull the container image.
    # if we set up a nat gateway/instance this can just be set to disabled either way.
    logger.info(f'Starting task {task_definition} in cluster {cluster}...')
    tasks = ecs_client.run_task(
        cluster              = cluster,
        launchType           = 'FARGATE',
        taskDefinition       = task_definition,
        count                = 1,
        startedBy            = startedby_id,
        networkConfiguration = {
            'awsvpcConfiguration' : {
                'subnets'       :  task_subnets,
                'assignPublicIp': 'ENABLED'
            }
        }
    )
    return tasks['tasks'][0]

def stop_task(ecs_client, cluster: str, task_arn: str, reason: str):
    logger.info(f'Stopping task {task_arn} in cluster {cluster} becase: {reason}')
    ecs_client.stop_task(cluster=cluster, task=task_arn, reason=reason)

def get_timestamp(datetime_obj: datetime) -> int:
    return int(datetime_obj.timestamp())

def get_timestamp_now() -> int:
    return get_timestamp(datetime.utcnow())
    
def kc_finished_starting(logs_client, group: str, stream: str) -> bool:
    regex_match = r".*Import finished successfully"
    logger.info(f"Checking log group {group} and stream {stream} for logs that match 'started'")
    paginator = logs_client.get_paginator("filter_log_events")
    messages = []
    for logs in paginator.paginate(logGroupName=group, logStreamNames=[stream], filterPattern='"KC-SERVICES0032"'):
        messages += [ event['message'] for event in logs['events'] if re.match(regex_match, event['message']) ]
    return len(messages) >= 1

def get_task(ecs_client, cluster: str, task_arn: str) -> dict:
    tasks = ecs_client.describe_tasks(cluster=cluster, tasks=[task_arn])['tasks']
    return tasks[0]

def taken_too_long(start_time: int, ttl_minutes: int = 5) -> bool:
    return (get_timestamp_now() - start_time) > (ttl_minutes * 60 * 1000)