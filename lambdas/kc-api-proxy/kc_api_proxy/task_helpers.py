import os, logging, time
from typing import List,Tuple
from datetime import datetime,timedelta
from .apiproxy import KeyCloakApiProxy

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

def assemble_ssm_path(ssm_prefix: str, realm_name: str, client_id: str) -> str:
    #normalizing leading/trailing slashes
    ssm_prefix = '/' + ssm_prefix.strip('/')
    # cfn template and this function both need to know how to assemble path right now :(
    # template has the dep around granting lambda role privs for the admin client
    return '/'.join([ssm_prefix, realm_name, client_id])

def clear_all_realms_cache(kc: KeyCloakApiProxy):
    realms = kc.get_realms()
    for realm in realms:
        realm_name = realm['realm']
        kc.clear_realm_cache(realm_name)

def clear_all_users_cache(kc: KeyCloakApiProxy):
    realms = kc.get_realms()
    for realm in realms:
        realm_name = realm['realm']
        kc.clear_user_cache(realm_name)

def rotate_and_store_client_secrets(kc: KeyCloakApiProxy, ssm_client, ssm_prefix: str):
    realms = kc.get_realms()
    for realm in realms:
        realm_name = realm['realm']
        for client in kc.get_clients(realm_name):
            secret = kc.rotate_secret(realm_name, client['id'])
            ssm_path = assemble_ssm_path(ssm_prefix, realm_name, client['clientId'])
            logger.info(f"Persisting rotated secret for {client['clientId']} ({client['id']}) to {ssm_path}")
            ssm_client.put_parameter(
                Name=ssm_path, 
                Description='Keycloak client secret source of truth',
                Value=secret['value'],
                Type='SecureString',
                Overwrite=True
            )

def remove_duplicate_users(kc: KeyCloakApiProxy, realm_name: str, usernames: List[str]):
    for username in usernames:
        try:
            kc.remove_user_by_username(realm_name, username)
        except Exception as e:
            logger.error(f"Failed to remove {username} from {realm_name}")
            pass

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
    start_time_epoch_ms = get_epoch_time_ms(start_time)
    end_time_epoch_ms = get_epoch_time_ms(end_time)
    filter_pattern = '"federated_identity_account_exists"'
    logger.info(f"Checking log group {group} and stream prefix {stream_prefix} for logs that match '{filter_pattern}'")
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

def convert_log_message_to_dict(message: str) -> dict:
    segments = message.split(', ')
    log_dict = dict()
    segments[0] = segments[0].split(' ')[-1]
    for segment in segments:
        if '=' not in segment:
            continue
        k,v = segment.split('=',1)
        log_dict[k] = v
    return log_dict

def parse_user_location_from_log_message(message: str) -> Tuple[str,str]:
    log_dict = convert_log_message_to_dict(message)
    return (log_dict['realmId'], log_dict['userId'])

def get_duplicate_user_locations(ecs_client, logs_client, task_definition_arn: str, start_time: datetime, end_time: datetime = None ):
    start_time = datetime.now() - timedelta(minutes=search_minutes_ago)
    user_locations = [ ]
    for log_group,log_prefix in get_log_locations_from_task_definition(ecs_client, task_definition_arn):
        duplicate_user_messages = get_duplicate_user_log_messages(logs_client, log_group, log_prefix, start_time)
        user_locations = user_locations + [ parse_user_location_from_log_message(message) for message in duplicate_user_messages ]
    return dedup_simple_list(user_locations)
