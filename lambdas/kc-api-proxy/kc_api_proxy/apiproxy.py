import requests, json, datetime, logging
from urllib.parse import urlencode, quote_plus, urlparse
from typing import List, Union

class KeyCloakApiProxy( ):
    def __init__(self, base_url: str, client_id: str, secret: str, logger = None):
        parsed_url = urlparse(base_url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/auth"
        self.set_credentials(client_id, secret)
        self.verify_ssl = True if parsed_url.hostname != 'localhost' else False
        self.logger = logger or logging.getLogger(__name__)

    def _get_updated_credentials(self) -> tuple:
        # should return tuple of (client_id,secret)
        # used to allow the class to check for rotated client creds if Invalid Client Secret is thrown as a request error
        logging.warn(f"Default implementation of {__name__} return already set creds; override if needed")
        return self._get_credentials()    

    def _get_credentials(self) -> tuple:
        return (self.client_id, self.secret)

    def _set_token_info(self, token: dict, from_time: datetime.datetime = datetime.datetime.utcnow() ):
        self.access_token = token['access_token']
        self.refresh_token = token['refresh_token']
        self.token_refresh_expiration = from_time + datetime.timedelta(seconds=token['refresh_expires_in'])
        self.token_expiration = from_time + datetime.timedelta(seconds=token['expires_in'])

    def _get_access_token(self) -> str:
        return self.access_token

    def _get_refresh_token(self) -> str:
        return self.refresh_token

    def _access_token_invalid(self, from_time: datetime.datetime = datetime.datetime.utcnow()) -> bool:
        return not self.access_token or (self.token_refresh_expiration and self.token_refresh_expiration < from_time)

    def _token_refresh_expired(self, from_time: datetime.datetime = datetime.datetime.utcnow()) -> bool:
        return self.token_refresh_expiration and self.token_refresh_expiration < from_time

    def _token_expired(self, from_time: datetime.datetime = datetime.datetime.utcnow()) -> bool:
        return self.token_expiration < from_time

    def _get_auth_header( self ) -> dict:
        endpoint = '/realms/master/protocol/openid-connect/token'
        request_args = {
            'url'     :  f"{self.base_url}{endpoint}",
            'headers' : {
                'Content-Type' : 'application/x-www-form-urlencoded'
            },
            'verify'  : self.verify_ssl 
        }
        now = datetime.datetime.utcnow()
        if self._access_token_invalid(now):
            client_id, secret = self._get_credentials()
            self.logger.info(f"Creating new access token with user {client_id}")
            payload = "grant_type=client_credentials"
            r = requests.post( auth=(client_id, secret), data=bytes(payload.encode('utf-8')), **request_args )
            r.raise_for_status()
            self._set_token_info(r.json(), now)
        if self._token_expired(now):
            client_id, _ = self._get_credentials()
            self.logger.info(f"Cached access token has expired for {client_id}; refreshing it")
            payload = f"refresh_token={self._get_refresh_token()}&client_id={client_id}&grant_type=refresh_token"
            r = requests.post( data=bytes(payload.encode('utf-8')), **request_args )
            r.raise_for_status()
            self._set_token_info(r.json(), now)
        return {"Authorization": f"Bearer {self._get_access_token()}"}


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
            auth_headers = self._get_auth_header( )
            auth_headers.update(headers)
            request_args['headers'] = auth_headers
            # might be a bad idea for both security and random serialization?
            self.logger.debug(f"Making keycloak api request: {request_args}")
            r = requests.request(**request_args)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and e.response.json()['error_description'] == 'Invalid client secret':
                new_client_id, new_secret = self._get_updated_credentials()
                current_client_id, current_secret = self._get_credentials()
                if new_client_id != current_client_id or new_secret != current_secret:
                    self.set_credentials(new_client_id, new_secret)
                    r = self._make_request(method, endpoint, query_params, body, headers)
                    pass
                else:
                    self.logger.error(f"Client secret access failed for both default secret and value from credenital refresh hook")
                    raise
            else:
                self.logger.exception(e)
                raise

        return r

    def _get_clients(self, realm_name: str, params: dict):
        endpoint = f"/admin/realms/{realm_name}/clients"
        self.logger.debug(f"Fetching clients for {realm_name} with params: {params}")
        return self._make_request('GET', endpoint, params)

    def set_credentials(self, client_id: str, secret: str) -> None:
        self.secret = secret
        # should pass through once tested
        self.client_id = client_id
        self.access_token = self.token_refresh_expiration = self.token_expiration = self.refresh_token = None

    def get_client(self, realm_name: str, client_name: str) -> dict:
        self.logger.info(f"Fetching client '{client_name}' from realm '{realm_name}'")
        r = self._get_clients(realm_name, {'clientId': client_name, 'viewableOnly': True})
        response = r.json()
        if len(response) < 1:
            message = f"Client '{client_name}' was not found in realm '{realm_name}'"
            self.logger.error(message)
            raise RuntimeError(message)
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
