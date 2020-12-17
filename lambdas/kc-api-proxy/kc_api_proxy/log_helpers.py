import os, logging, time
from typing import List,Tuple
from datetime import datetime,timedelta

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

def get_epoch_time_ms(date_time: datetime = None):
    date_time = date_time or datetime.now()
    return int(date_time.timestamp() * 1000)

# hacky dedup helper.. probably not very efficient?
def dedup_simple_list(simple_list: List) -> List:
    return list(set(simple_list))

# A bit gold-plated. It handles multiple different log locations being specified
# in a single task definition which we aren't doing at all..
# Also should depup the results... which should never be multiple
# Return ex
#    [('/ecs/keycloak-psychic-potato', 'kc-app')]
def get_log_locations_from_task_definition(ecs_client, task_definition_arn: str) -> List[Tuple[str,str]]:
    task_def = ecs_client.describe_task_definition(taskDefinition=task_definition_arn)
    return dedup_simple_list( 
        [ 
            (container_def['logConfiguration']['options']['awslogs-group'],container_def['logConfiguration']['options']['awslogs-stream-prefix']) 
            for container_def in task_def['taskDefinition']['containerDefinitions'] 
        ] 
    )


def get_duplicate_user_log_messages(logs_client, group: str, stream_prefix: str, start_time: datetime, end_time: datetime = None ) -> List[dict]:
    end_time = end_time or datetime.now()
    start_time_epoch_ms = get_epoch_time_ms(start_time)
    end_time_epoch_ms = get_epoch_time_ms(end_time)
    filter_pattern = '"federated_identity_account_exists"'
    logger.info(f"Checking log group {group} and stream prefix {stream_prefix} for logs that match '{filter_pattern}' between {start_time} and {end_time}")
    paginator = logs_client.get_paginator("filter_log_events")
    filter_kwargs = {
        'logGroupName'       : group, 
        'logStreamNamePrefix': stream_prefix, 
        'filterPattern'      : filter_pattern,
        'startTime'          : start_time_epoch_ms,
        'endTime'            : end_time_epoch_ms
    }
    messages = []
    for logs in paginator.paginate(**filter_kwargs):
        messages += [ event['message'] for event in logs['events'] ]
    return messages

# log ex:
#   16:01:27,100 WARN  [org.keycloak.events] (default task-1493) type=IDENTITY_PROVIDER_FIRST_LOGIN_ERROR, realmId=navex, clientId=cmd-backend, userId=1fc3d2c0-f472-4e6d-8d7e-86553caa499d, ipAddress=24.173.19.238, error=federated_identity_account_exists, identity_provider=doorman, existing_username=c75c8c04-a60d-eb11-a96a-0050568ba3ec, redirect_uri=https://maint.policytech.com/oidc/coderedirector/?ReturnUrl=https%3a%2f%2faplusfcu.policytech.com%2foidc%2fcodeconsumer%2f%3fReturnUrl%3d%252fdotNet%252fdocuments%252f%253fdocid%253d10910, identity_provider_identity=c75c8c04-a60d-eb11-a96a-0050568ba3ec, code_id=d9bca038-41d7-4b20-ad7a-2c193f01e35d, authSessionParentId=d9bca038-41d7-4b20-ad7a-2c193f01e35d, authSessionTabId=zVdvJj48L5Y
def convert_log_message_to_dict(message: str) -> dict:
    segments = message.split(', ')
    log_dict = dict()
    # throws away info before the key=value formatting. Maybe should keep but it isn't needed now and i wasn't
    # sure how reliable the log structure is in this area to write one off cases for 
    segments[0] = segments[0].split(' ')[-1]
    for segment in segments:
        if '=' not in segment:
            continue
        k,v = segment.split('=',1)
        log_dict[k] = v
    return log_dict

# Need to double check, but i think what is logged as userId is actually the username
# and there is a seperate userId that kc uses internally :/
def parse_user_location_from_log_message(message: str) -> Tuple[str,str]:
    log_dict = convert_log_message_to_dict(message)
    return (log_dict['realmId'], log_dict['userId'])

def get_duplicate_user_locations(ecs_client, logs_client, task_definition_arn: str, start_time: datetime, end_time: datetime = None ):
    user_locations = [ ]
    for log_group,log_prefix in get_log_locations_from_task_definition(ecs_client, task_definition_arn):
        duplicate_user_messages = get_duplicate_user_log_messages(logs_client, log_group, log_prefix, start_time, end_time)
        user_locations = user_locations + [ parse_user_location_from_log_message(message) for message in duplicate_user_messages ]
    return dedup_simple_list(user_locations)