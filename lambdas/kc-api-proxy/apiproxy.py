import requests, os, json, boto3, datetime
from urllib.parse import urlencode, quote_plus, urlparse
from typing import List, Union

ssm_client = boto3.client('ssm')

class KeyCloakApiProxy():
    def __init__(self, base_url: str, username: str, password: str):
        parsed_url = urlparse(base_url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/auth"
        self.username = username
        self.password = password
        self.scheme = parsed_url.scheme
        self.verify_ssl = True if parsed_url.hostname != 'localhost' else False
        self.access_token = self.token_refresh_expiration = None
        self.navex_realm = 'navex'


    def _get_auth_header(self) -> dict:
        endpoint = '/realms/master/protocol/openid-connect/token'
        request_args = {
            'url'     :  f"{self.base_url}{endpoint}",
            'headers' : {
                'Content-Type' : 'application/x-www-form-urlencoded'
            },
            'verify'  : self.verify_ssl 
        }
        now = datetime.datetime.utcnow()
        if not self.access_token or (self.token_refresh_expiration and self.token_refresh_expiration < now):
            print("Creating initial access token..")
            payload = f"username={self.username}&password={self.password}&client_id=admin-cli&grant_type=password"
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
        query_params = '' if not query_params else '?' + urlencode(query_params, quote_via=quote_plus)
        request_args = {
            'verify'  : self.verify_ssl,
            'url'     : f"{self.base_url}{endpoint}{query_params}"
        }
        # probably not a great approach.. should just make it dependent on if body was passed in
        if method != 'GET':
            if isinstance(body,dict):
                request_args['data'] = json.dumps(body)
            elif isinstance(body,str):
                request_args['data'] = bytes(body.encode('utf-8'))
            elif isinstance(body,bytes):
                request_args['data'] = body

        auth_headers = self._get_auth_header()
        auth_headers.update(headers)
        request_args['headers'] = auth_headers
        r = requests.request(method, **request_args)
        r.raise_for_status()
        return r

    def _get_clients(self, params: dict):
        endpoint = f"/admin/realms/{self.navex_realm}/clients"
        return self._make_request('GET', endpoint, params)

    def get_client(self, client_name: str) -> dict:
        r = self._get_clients({'clientId': client_name, 'viewableOnly': True})
        response = r.json()
        if len(response) < 1:
            raise RuntimeError(f"Client {client_name} was not found")
        return response[0]

    def get_clients( self ) -> List[dict] :
        r = self._get_clients({'viewableOnly': True})
        return r.json()

    def rotate_secret(self, client_id: str) -> dict:
        endpoint = f"/admin/realms/{self.navex_realm}/clients/{client_id}/client-secret"
        r = self._make_request('POST', endpoint)
        return r.json()

    def clear_realm_cache(self, realm_name: str = None) -> None:
        realm_name = realm_name or self.navex_realm
        endpoint = f"/admin/realms/{realm_name}/clear-realm-cache"
        self._make_request('POST', endpoint)
    
    def clear_user_cache(self, realm_name: str = None) -> None:
        realm_name = realm_name or self.navex_realm
        endpoint = f"/admin/realms/{realm_name}/clear-user-cache"
        self._make_request('POST', endpoint)

def rotate_and_store_client_keys(kc: KeyCloakApiProxy, ssm_prefix: str):
    for client in kc.get_clients():
        secret = kc.rotate_secret(client['id'])
        ssm_path = f"{ssm_prefix}/{client['clientId']}"
        print(f"Persisting rotated secret for {client['clientId']} ({client['id']}) to {ssm_prefix}...")
        ssm_client.put_parameter(
            Name=ssm_path, 
            Description='Keycloak client secret source of truth',
            Value=secret['value'],
            Type='SecureString',
            Overwrite=True
        )

def lambda_handler(event, context):
    base_url = os.environ['KeyCloakBaseUrl']
    user_name = os.environ['AdminUserName']
    password = os.environ['AdminPassword']
    ssm_prefix = os.environ['SsmPrefix'].rstrip('/')
    kc = KeyCloakApiProxy(base_url, user_name, password)
    rotate_and_store_client_keys(kc, ssm_prefix)

"""
kc_api = KeyCloakApiProxy('https://localhost:8443', 'dvader', 'password')
rotate_and_store_client_keys(kc_api, '/weston/keycloak/client-keys')
"""