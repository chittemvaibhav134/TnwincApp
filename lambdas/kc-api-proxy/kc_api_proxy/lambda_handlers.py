import os, boto3, logging
from .apiproxy import KeyCloakApiProxy
from .cpresponse import CodePipelineHelperResponse
from . import get_logger

ssm_client = boto3.client('ssm')
logger = get_logger(__name__)

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

def rotate_and_store_client_secrets(kc: KeyCloakApiProxy, ssm_prefix: str):
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

def get_keycloak_api_proxy_from_env() -> KeyCloakApiProxy:
    base_url = os.environ['KeyCloakBaseUrl']
    client_id = os.environ['AdminClientId']
    default_secret = os.environ['AdminDefaultSecret']
    ssm_prefix = os.environ['SsmPrefix']
    admin_secret_ssm_path =  assemble_ssm_path(ssm_prefix, 'master', client_id)
    return KeyCloakApiProxy(base_url, client_id, default_secret, ssm_client, admin_secret_ssm_path)

# This entry point will be called by a scheduled cloudwatch job
# Should probably catch exceptions and return whatever lambdas ought to return...
def cwe_rotate_handler(event, context):
    logger.info("Cloudwatch scheduled secret rotation started")
    kc = get_keycloak_api_proxy_from_env()
    rotate_and_store_client_secrets(kc, os.environ['SsmPrefix'])
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
                rotate_and_store_client_secrets(kc, os.environ['SsmPrefix'])
            if 'clear_realm_cache' == action:
                clear_all_realms_cache(kc)
        except Exception as e:
            logger.exception(e)
            return CodePipelineHelperResponse.failed(f"Error performing action {action}: {e}")
    return CodePipelineHelperResponse.succeeded(f"Successfully performed actions: {actions}")