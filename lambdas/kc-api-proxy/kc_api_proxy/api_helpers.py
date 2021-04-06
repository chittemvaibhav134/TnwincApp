import os, logging
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
        confidential_clients = [ client for client in kc.get_clients(realm_name) if not client['publicClient'] and not client['bearerOnly'] ]
        for client in confidential_clients:
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