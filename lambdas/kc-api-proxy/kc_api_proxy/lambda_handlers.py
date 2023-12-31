import os, boto3, logging
from datetime import datetime
from .apiproxy import KeyCloakApiProxy
from .cpresponse import CodePipelineHelperResponse
from .log_helpers import get_duplicate_user_locations
from .api_helpers import (
    assemble_ssm_path, 
    rotate_and_store_client_secrets, 
    clear_all_users_cache
)

ssm_client = boto3.client('ssm')
sns_client = boto3.client('sns')
logs_client = boto3.client('logs')
ecs_client = boto3.client('ecs')

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

class KcApiProxySsmRefresh(KeyCloakApiProxy):
    def _get_updated_credentials(self):
        ssm_secret_path = os.environ['AdminSecretSsmPath']
        self.logger.info(f"Checking ssm {ssm_secret_path} for updated client secret")
        secret = ssm_client.get_parameter(
            Name=ssm_secret_path,
            WithDecryption=True
        )['Parameter']['Value']
        return (os.environ['AdminClientId'], secret)

def get_keycloak_api_proxy_from_env() -> KcApiProxySsmRefresh:
    base_url = os.environ['KeyCloakBaseUrl']
    client_id = os.environ['AdminClientId']
    default_secret = os.environ['AdminDefaultSecret']
    return KcApiProxySsmRefresh(base_url, client_id, default_secret, logger)

# This entry point will be called by a scheduled cloudwatch job
# Should probably catch exceptions and return whatever lambdas ought to return...
def cwe_rotate_handler(event, context):
    logger.info("Cloudwatch scheduled secret rotation started")
    kc = get_keycloak_api_proxy_from_env()
    rotate_and_store_client_secrets(kc, ssm_client, sns_client, os.environ['SsmPrefix'], os.environ['RotateSecretTopicArn'])
    logger.info("Cloudwatch scheduled secret rotation finished")

def get_search_times_from_alarm_event(event):
    current_state_time = event['detail']['state']['timestamp']
    last_state_time = event['detail'].get('previousState',{}).get('timestamp', current_state_time)
    return ( datetime.strptime(last_state_time, "%Y-%m-%dT%H:%M:%S.%f+0000"), datetime.strptime(current_state_time, "%Y-%m-%dT%H:%M:%S.%f+0000") )
    

def cwe_remove_duplicant_users_alarm_handler(event, context):
    if event.get('detail-type') != 'CloudWatch Alarm State Change':
        logger.warn("Unexpected event type triggered lambda..")
        logger.warn(event)
        return
    logger.info("Searching for duplicate users in logs..")
    keycloak_app_task_definition_arn = os.environ['TaskDefinitionArn']
    start_time, end_time = get_search_times_from_alarm_event(event)
    duplicate_user_locations = get_duplicate_user_locations(ecs_client, logs_client, keycloak_app_task_definition_arn, start_time, end_time)
    logger.info(f"Found {len(duplicate_user_locations)} duplicate user id(s) blocked from loggin in")
    kc = get_keycloak_api_proxy_from_env()
    for realm_name, user_id in duplicate_user_locations:
        try:
            kc.remove_user_by_id(realm_name, user_id)
        except Exception as e:
            logger.error(f"Failed to remove '{user_id}' from '{realm_name}'")
            logger.exception(e)
            pass

# This entry point will be called by codepipeline directly to cause
# client secrets to rotate immediately following a deployment since they 
# will get reset as is
# it returns a dict expected by the CPInvokeLambda action
def cp_post_deploy_handler(event, context):
    actions = list(set([ action.lower() for action in event.get('Actions',[]) ]))
    supported_actions = ['rotate_client_secrets','clear_realm_cache','clear_user_cache']
    unsupported_actions = [action for action in actions if action not in supported_actions]
    logger.info(f"Codepipeline post-deploy started for actions: {actions}")
    
    if unsupported_actions:
        logger.error(f"Called with unsupported action(s) {unsupported_actions}")
        return CodePipelineHelperResponse.failed(f"Called with unsupported actions. Supported actions: {supported_actions}. Unsupported actions: {unsupported_actions}")
    
    try:
        kc = get_keycloak_api_proxy_from_env()
    except Exception as e:
        logger.exception(e)
        return CodePipelineHelperResponse.failed(f"Error creating keycloak api proxy from env: {e}")

    # Always clear realm cache. I think importing the config easily leads to 
    # the ids not matching in db vs app cache and then rotating the secrets (or anything else hitting a client-id)
    # has a solid chance of of throwing a 500 :/
    try:
        kc.clear_realm_cache("master")
        # reset the kc api proxy because once the master realm cache has been cleared
        # it will notice that the admin-api-proxy secret has been reset and no longer matches what was pulled 
        # from ssm.. which causes this to fail every deploy, but succeed on retrying the action.
        # If we introduce more realms it is probably worth using the clear_all_realms_cache task_helper instead
        # of hardcoding the two known ones
        kc = get_keycloak_api_proxy_from_env()
        kc.clear_realm_cache("navex")
    except Exception as e:
        logger.exception(e)
        return CodePipelineHelperResponse.failed(f"Error clearing realm cache pre deploy actions: {e}")

    if not actions:
        logger.warning("Post deploy lambda was invoked without any 'Actions'")
        return CodePipelineHelperResponse.succeeded("No-op due to no actions begin specified")

    for action in actions:
        try:
            if 'rotate_client_secrets' == action:
                rotate_and_store_client_secrets(kc, ssm_client, sns_client, os.environ['SsmPrefix'], os.environ['RotateSecretTopicArn'])
            if 'clear_user_cache' == action:
                clear_all_users_cache(kc)
        except Exception as e:
            logger.exception(e)
            return CodePipelineHelperResponse.failed(f"Error performing action {action}: {e}")

    try:
        kc.clear_realm_cache("master")
        kc.clear_realm_cache("navex")
    except Exception as e:
        logger.exception(e)
        return CodePipelineHelperResponse.failed(f"Error clearing realm cache post deploy actions: {e}")

    return CodePipelineHelperResponse.succeeded(f"Successfully performed actions: {actions}")