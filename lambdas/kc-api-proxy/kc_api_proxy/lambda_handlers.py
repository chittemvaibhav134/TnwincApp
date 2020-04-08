import os, boto3, logging
from .apiproxy import KeyCloakApiProxy
from .cpresponse import CodePipelineHelperResponse
from .task_helpers import (
    assemble_ssm_path, 
    rotate_and_store_client_secrets, 
    clear_all_users_cache
)

ssm_client = boto3.client('ssm')
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
                rotate_and_store_client_secrets(kc, ssm_client, os.environ['SsmPrefix'])
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