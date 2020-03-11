import requests, os, json, boto3, datetime
from urllib.parse import urlencode, quote_plus, urlparse
from typing import List, Union

ssm_client = boto3.client('ssm')

class KeyCloakApiProxy():
    def __init__(self, base_url: str, client_id: str, default_secret: str, ssm_secret_path: str):
        parsed_url = urlparse(base_url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/auth"
        self.client_id = client_id
        self.default_secret = self.secret = default_secret
        self.ssm_secret_path = ssm_secret_path
        self.scheme = parsed_url.scheme
        self.verify_ssl = True if parsed_url.hostname != 'localhost' else False
        self.access_token = self.token_refresh_expiration = None

    def _retrieve_secret_from_ssm(self):
        parameter = ssm_client.get_parameter(
            Name=self.ssm_secret_path,
            WithDecryption=True
        )
        return parameter['Parameter']['Value']

    def _get_auth_header(self, secret: str) -> dict:
        endpoint = '/realms/master/protocol/openid-connect/token'
        request_args = {
            'url'     :  f"{self.base_url}{endpoint}",
            'headers' : {
                'Content-Type' : 'application/x-www-form-urlencoded'
            },
            'auth': (self.client_id, secret),
            'verify'  : self.verify_ssl 
        }
        now = datetime.datetime.utcnow()
        if not self.access_token or (self.token_refresh_expiration and self.token_refresh_expiration < now):
            print("Creating initial access token..")
            payload = f"grant_type=client_credentials"
            r = requests.post( data=bytes(payload.encode('utf-8')), **request_args )
            r.raise_for_status()
            self.access_token = r.json()
            self.token_expiration = now + datetime.timedelta(seconds=self.access_token['expires_in'])
            self.token_refresh_expiration = now + datetime.timedelta(seconds=self.access_token['refresh_expires_in'])
            
        if self.token_expiration < now:
            print("Cached access token has expired; refreshing now...")
            payload = f"refresh_token={self.access_token['refresh_token']}&client_id=admin-cli&grant_type=refresh_token"
            r = requests.post( data=bytes(payload.encode('utf-8')), **request_args )
            r.raise_for_status()
            self.access_token = r.json()
            self.token_expiration = now + datetime.timedelta(seconds=self.access_token['expires_in'])
        return {"Authorization": f"Bearer {self.access_token['access_token']}"}


    def _make_request(self, method: str, endpoint: str, query_params: dict = None, body: Union[dict,str,bytes] = None, headers: dict = None):
        method = method.upper()
        body = body or {}
        # questionable default...
        headers = headers or {'Content-Type' : 'application/json'}
        query_param_string = '' if not query_params else '?' + urlencode(query_params, quote_via=quote_plus)
        request_args = {
            'verify'  : self.verify_ssl,
            'url'     : f"{self.base_url}{endpoint}{query_param_string}"
        }
        # probably not a great approach.. should just make it dependent on if body was passed in
        if method != 'GET':
            if isinstance(body,dict):
                request_args['data'] = json.dumps(body)
            elif isinstance(body,str):
                request_args['data'] = bytes(body.encode('utf-8'))
            elif isinstance(body,bytes):
                request_args['data'] = body
        try:
            auth_headers = self._get_auth_header(self.secret)
            auth_headers.update(headers)
            request_args['headers'] = auth_headers
            r = requests.request(method, **request_args)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and e.response.json()['error_description'] == 'Invalid client secret':
                if self.secret == self.default_secret:
                    print(f"Client secret access failed; fetching secret from ssm and retrying request...")
                    self.secret = self._retrieve_secret_from_ssm()
                    r = self._make_request(method, endpoint, query_params, body, headers)
                    pass
                else:
                    print(f"Client secret access failed for both default secret and value in ssm...")
                    raise
            else:
                raise
        return r

    def _get_clients(self, realm_name: str, params: dict):
        endpoint = f"/admin/realms/{realm_name}/clients"
        return self._make_request('GET', endpoint, params)

    def get_client(self, realm_name: str, client_name: str) -> dict:
        r = self._get_clients(realm_name, {'clientId': client_name, 'viewableOnly': True})
        response = r.json()
        if len(response) < 1:
            raise RuntimeError(f"Client {client_name} was not found")
        return response[0]

    def get_clients( self, realm_name: str ) -> List[dict] :
        r = self._get_clients(realm_name, {'viewableOnly': True})
        return r.json()

    def rotate_secret(self, realm_name: str, client_id: str) -> dict:
        endpoint = f"/admin/realms/{realm_name}/clients/{client_id}/client-secret"
        r = self._make_request('POST', endpoint)
        return r.json()

    def clear_realm_cache(self, realm_name: str) -> None:
        endpoint = f"/admin/realms/{realm_name}/clear-realm-cache"
        self._make_request('POST', endpoint)
    
    def clear_user_cache(self, realm_name: str) -> None:
        endpoint = f"/admin/realms/{realm_name}/clear-user-cache"
        self._make_request('POST', endpoint)

    def get_realms(self):
        endpoint = f"/admin/realms"
        r = self._make_request('GET', endpoint)
        return r.json()

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

def lambda_handler(event, context):
    base_url = os.environ['KeyCloakBaseUrl']
    client_id = os.environ['AdminClientId']
    default_secret = os.environ['AdminDefaultSecret']
    ssm_prefix = os.environ['SsmPrefix']
    # I think master is safe to hardcode.. if not i need to pass it into the auth bit as an arg
    admin_secret_ssm_path =  assemble_ssm_path(ssm_prefix, 'master', client_id)
    kc = KeyCloakApiProxy(base_url, client_id, default_secret, admin_secret_ssm_path)
    rotate_and_store_client_secrets(kc, ssm_prefix)
    

"""
from apiproxy import *
client_id = 'admin-cli'
default_secret = '6fcd132c-9ad5-4a09-b0a3-078e20531e3b'
ssm_prefix = '/weston/keycloak/client-keys'
admin_secret_ssm_path =  assemble_ssm_path(ssm_prefix, 'master', client_id)
kc = KeyCloakApiProxy('https://localhost:8443', client_id, default_secret, admin_secret_ssm_path)
"""