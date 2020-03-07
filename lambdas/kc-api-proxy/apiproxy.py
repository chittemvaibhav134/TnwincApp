import requests, os, json
from urllib.parse import urlencode, quote_plus

def get_request_config() -> dict:
    scheme = os.environ.get('SCHEME', 'https')
    domain = os.environ.get('DOMAIN','localhost')
    port = os.environ.get('PORT', '8443')
    verify_ssl = True if domain != 'localhost' else False
    return {
        'base_url'  : f"{scheme}://{domain}:{port}/auth",
        'username'  : os.environ.get('ADMINUSERNAME', 'dvader'),
        'password'  : os.environ.get('ADMINPASSWORD', 'password'),
        'realm'     : 'navex',
        'verify_ssl': verify_ssl
    }

def get_token(config: dict = None) -> dict:
    config = config or get_request_config()
    endpoint = '/realms/master/protocol/openid-connect/token'
    payload = f"username={config['username']}&password={config['password']}&client_id=admin-cli&grant_type=password"
    request_args = {
        'url'     :  f"{config['base_url']}{endpoint}",
        'data'    : bytes(payload.encode('utf-8')),
        'headers' : {
            'Content-Type' : 'application/x-www-form-urlencoded'
        },
        'verify'  : config['verify_ssl'] 
    }
    r = requests.post( **request_args )
    r.raise_for_status()
    return r.json()

def _get_clients(config: dict, access_token: str, params: dict):
    query_params = '' if not params else '?' + urlencode(params, quote_via=quote_plus) 
    endpoint = f"/admin/realms/{config['realm']}/clients"
    request_args = {
        'url'     :  f"{config['base_url']}{endpoint}{query_params}",
        'headers' : {
            'Content-Type' : 'application/json',
            'Authorization': f"Bearer {access_token}"
        },
        'verify'  : config['verify_ssl'] 
    }
    return requests.get(**request_args)

def get_client(client_id: str, config: dict = None, access_token: str=None):
    config = config or get_request_config()
    access_token = access_token or get_token(config)['access_token']
    r = _get_clients(config, access_token, {'clientId': client_id, 'viewableOnly': True})
    r.raise_for_status()
    return r.json()

def get_clients(config: dict = None, access_token: str=None):
    config = config or get_request_config()
    access_token = access_token or get_token(config)['access_token']
    r = _get_clients(config, access_token, {'viewableOnly': True})
    r.raise_for_status()
    return r.json()

def rotate_secret(client_id: str, config: dict = None, access_token: str=None):
    config = config or get_request_config()
    access_token = access_token or get_token(config)['access_token']
    endpoint = f"/admin/realms/{config['realm']}/clients/{client_id}/client-secret"
    request_args = {
        'url'     :  f"{config['base_url']}{endpoint}",
        'data'    : json.dumps({}),
        'headers' : {
            'Content-Type' : 'application/json',
            'Authorization': f"Bearer {access_token}"
        },
        'verify'  : config['verify_ssl'] 
    }
    r = requests.post(**request_args)
    r.raise_for_status()
    return r.json()