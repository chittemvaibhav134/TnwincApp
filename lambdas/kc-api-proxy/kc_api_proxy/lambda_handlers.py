import os, boto3
from .apiproxy import KeyCloakApiProxy
from .cpresponse import CodePipelineHelperResponse

ssm_client = boto3.client('ssm')

def assemble_ssm_path(ssm_prefix: str, realm_name: str, client_id: str) -> str:
    #normalizing leading/trailing slashes
    ssm_prefix = '/' + ssm_prefix.strip('/')
    # cfn template and this function both need to know how to assemble path right now :(
    # template has the dep around granting lambda role privs for the admin client
    return '/'.join([ssm_prefix, realm_name, client_id])
    
def rotate_and_store_client_secrets(kc: KeyCloakApiProxy, ssm_prefix: str):
    realms = kc.get_realms()
    for realm in realms:
        realm_name = realm['realm']
        for client in kc.get_clients(realm_name):
            secret = kc.rotate_secret(realm_name, client['id'])
            ssm_path = assemble_ssm_path(ssm_prefix, realm_name, client['clientId'])
            print(f"Persisting rotated secret for {client['clientId']} ({client['id']}) to {ssm_path}...")
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
    kc = get_keycloak_api_proxy_from_env()
    rotate_and_store_client_secrets(kc, os.environ['SsmPrefix'])

# This entry point will be called by codepipeline directly to cause
# client secrets to rotate immediately following a deployment since they 
# will get reset as is
# it returns a dict expected by the CPInvokeLambda action
def cp_rotate_handler(event, context):
    try:
        kc = get_keycloak_api_proxy_from_env()
    except Exception as e:
        return CodePipelineHelperResponse.failed(f"Error creating keycloak api proxy from env: {e}")
    try:
        rotate_and_store_client_secrets(kc, os.environ['SsmPrefix'])
    except Exception as e:
        return CodePipelineHelperResponse.failed(f"Error rotating keycloak client secrets: {e}")
    # potentially want to tack this on here for dumb cache reasons
    # kc.clear_realm_cache()
    return CodePipelineHelperResponse.succeeded("Successfully rotated all client secrets")