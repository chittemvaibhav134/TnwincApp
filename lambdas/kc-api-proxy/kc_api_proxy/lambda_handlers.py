import os, boto3, logging
from .apiproxy import KeyCloakApiProxy
from .cpresponse import CodePipelineHelperResponse
from .task_helpers import (
    assemble_ssm_path, 
    rotate_and_store_client_secrets, 
    clear_all_realms_cache
)

ssm_client = boto3.client('ssm')
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

def get_keycloak_api_proxy_from_env() -> KeyCloakApiProxy:
    base_url = os.environ['KeyCloakBaseUrl']
    user = os.environ['AdminUser']
    password_ssm_path = os.environ['AdminPasswordSsmPath']
    password = ssm_client.get_parameter(
        Name=password_ssm_path,
        WithDecryption=True
    )['Parameter']['Value']
    return KeyCloakApiProxy(base_url, user, password, logger)

# This entry point will be called by a scheduled cloudwatch job
# Should probably catch exceptions and return whatever lambdas ought to return...
def cwe_rotate_handler(event, context):
    logger.info("Cloudwatch scheduled secret rotation started")
    kc = get_keycloak_api_proxy_from_env()
    rotate_and_store_client_secrets(kc, ssm_client, os.environ['SsmPrefix'])
    logger.info("Cloudwatch scheduled secret rotation finished")

# This entry point will be called by codepipeline directly to cause
# client secrets to rotate immediately following a deployment since they 
# will get reset as is
# it returns a dict expected by the CPInvokeLambda action
def cp_post_deploy_handler(event, context):
    actions = list(set([ action.lower() for action in event.get('Actions',[]) ]))
    supported_actions = ['rotate_client_secrets','clear_realm_cache','clear_user_cache']
    unsupported_actions = [action for action in actions if action not in supported_actions]
    logger.info(f"Codepipeline post-deploy started for actions: {actions}")
    if not actions:
        logger.warn("Post deploy lambda was invoked without any 'Actions'")
        return CodePipelineHelperResponse.succeeded("No-op due to no actions begin specified")

    if unsupported_actions:
        logger.error(f"Called with unsupported action(s) {unsupported_actions}")
        return CodePipelineHelperResponse.failed(f"Called with unsupported actions. Supported actions: {supported_actions}. Unsupported actions: {unsupported_actions}")
    
    try:
        kc = get_keycloak_api_proxy_from_env()
    except Exception as e:
        logger.exception(e)
        return CodePipelineHelperResponse.failed(f"Error creating keycloak api proxy from env: {e}")

    for action in actions:
        try:
            if 'rotate_client_secrets' == action:
                rotate_and_store_client_secrets(kc, ssm_client, os.environ['SsmPrefix'])
            if 'clear_realm_cache' == action:
                clear_all_realms_cache(kc)
        except Exception as e:
            logger.exception(e)
            return CodePipelineHelperResponse.failed(f"Error performing action {action}: {e}")
    return CodePipelineHelperResponse.succeeded(f"Successfully performed actions: {actions}")