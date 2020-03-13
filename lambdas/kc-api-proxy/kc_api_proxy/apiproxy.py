import requests, json, datetime
from urllib.parse import urlencode, quote_plus, urlparse
from typing import List, Union
from .logging_setup import get_logger

class KeyCloakApiProxy():
    def __init__(self, base_url: str, client_id: str, default_secret: str, ssm_client, ssm_secret_path: str, logger = None):
        parsed_url = urlparse(base_url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/auth"
        self.client_id = client_id
        self.secret = self.default_secret = default_secret
        self.ssm_client = ssm_client
        self.ssm_secret_path = ssm_secret_path
        self.scheme = parsed_url.scheme
        self.verify_ssl = True if parsed_url.hostname != 'localhost' else False
        self.access_token = self.token_refresh_expiration = None
        self.logger = logger or get_logger(__name__)

    def _retrieve_secret_from_ssm(self):
        self.logger.info(f"Fetching client secret for {self.client_id} from {self.ssm_secret_path}..")
        parameter = self.ssm_client.get_parameter(
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
            self.logger.info(f"Creating new access token with client id {self.client_id}")
            payload = f"grant_type=client_credentials"
            r = requests.post( data=bytes(payload.encode('utf-8')), **request_args )
            r.raise_for_status()
            self.access_token = r.json()
            self.token_expiration = now + datetime.timedelta(seconds=self.access_token['expires_in'])
            self.token_refresh_expiration = now + datetime.timedelta(seconds=self.access_token['refresh_expires_in'])
            
        if self.token_expiration < now:
            self.logger.info(f"Cached access token has expired for {self.client_id}; refreshing it")
            payload = f"refresh_token={self.access_token['refresh_token']}&client_id={self.client_id}&grant_type=refresh_token"
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
            'url'     : f"{self.base_url}{endpoint}{query_param_string}",
            'method'  : method
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
            self.logger.debug("Fetching authentication headers for keycloak api request")
            auth_headers = self._get_auth_header(self.secret)
            auth_headers.update(headers)
            request_args['headers'] = auth_headers
            # might be a bad idea for both security and random serialization?
            self.logger.debug(f"Making keycloak api request: {request_args}")
            r = requests.request(**request_args)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and e.response.json()['error_description'] == 'Invalid client secret':
                ssm_secret = self._retrieve_secret_from_ssm()
                if self.secret != ssm_secret:
                    self.logger.info(f"Client secret access failed; fetching secret from ssm and retrying request")
                    self.secret = ssm_secret
                    r = self._make_request(method, endpoint, query_params, body, headers)
                    pass
                else:
                    self.logger.error(f"Client secret access failed for both default secret and value in ssm")
                    raise
            else:
                self.logger.exception(e)
                raise
        return r

    def _get_clients(self, realm_name: str, params: dict):
        endpoint = f"/admin/realms/{realm_name}/clients"
        self.logger.debug(f"Fetching clients for {realm_name} with params: {params}")
        return self._make_request('GET', endpoint, params)

    def get_client(self, realm_name: str, client_name: str) -> dict:
        self.logger.info(f"Fetching client '{client_name}' from realm '{realm_name}'")
        r = self._get_clients(realm_name, {'clientId': client_name, 'viewableOnly': True})
        response = r.json()
        if len(response) < 1:
            self.logger.error(f"Client '{client_name}' was not found in realm '{realm_name}'")
            raise RuntimeError(f"Client {client_name} was not found")
        return response[0]

    def get_clients( self, realm_name: str ) -> List[dict]:
        self.logger.info(f"Fetching all clients from realm '{realm_name}'")
        r = self._get_clients(realm_name, {'viewableOnly': True})
        return r.json()

    def rotate_secret(self, realm_name: str, client_id: str) -> dict:
        self.logger.info(f"Rotating client secret for '{client_id}' from realm '{realm_name}'")
        endpoint = f"/admin/realms/{realm_name}/clients/{client_id}/client-secret"
        r = self._make_request('POST', endpoint)
        return r.json()

    def clear_realm_cache(self, realm_name: str) -> None:
        self.logger.info(f"Clearing realm cache for realm {realm_name}")
        endpoint = f"/admin/realms/{realm_name}/clear-realm-cache"
        self._make_request('POST', endpoint)
    
    def clear_user_cache(self, realm_name: str) -> None:
        self.logger.info(f"Clearing user cache for realm {realm_name}")
        endpoint = f"/admin/realms/{realm_name}/clear-user-cache"
        self._make_request('POST', endpoint)

    def get_realms(self):
        self.logger.info("Fetching all realms")
        endpoint = f"/admin/realms"
        r = self._make_request('GET', endpoint)
        return r.json()


"""
$env:PYTHONWARNINGS="ignore:Unverified HTTPS request"
$env:AWS_DEFAULT_REGION = "us-east-2"
Set-AwsSsoCreds -Account 'navexdev' -Role DevAccountAdministratorAccess -EnvironmentVariables
"""

"""
from apiproxy import *
client_id = 'admin-api-proxy'
default_secret = '4d1e3de1-6f61-46b1-92a8-e1eccce61559'
ssm_prefix = '/weston/keycloak/client-keys/master/admin-api-proxy'
#admin_secret_ssm_path =  assemble_ssm_path(ssm_prefix, 'master', client_id)
base_url = 'https://navex.id3.psychic-potato.navex-int.com'
kc = KeyCloakApiProxy(base_url, client_id, default_secret, admin_secret_ssm_path)
"""