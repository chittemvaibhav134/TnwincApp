import requests, json, datetime, logging
from urllib.parse import urlencode, quote_plus, urlparse
from typing import List, Union

class KeyCloakApiProxy( ):
    def __init__(self, base_url: str, client_id: str, secret: str, logger = None):
        parsed_url = urlparse(base_url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/auth"
        self._set_credentials(client_id, secret)
        self.verify_ssl = True if parsed_url.hostname != 'localhost' else False
        self.logger = logger or logging.getLogger(__name__)

    def _get_updated_credentials(self) -> tuple:
        # should return tuple of (client_id,secret)
        # used to allow the class to check for rotated client creds if Invalid Client Secret is thrown as a request error
        logging.warn(f"Default implementation of {__name__} return already set creds; override if needed")
        return self._get_credentials()    

    def _get_credentials(self) -> tuple:
        return (self.client_id, self.secret)

    def _set_token_info(self, token: dict, from_time: datetime.datetime = None ):
        from_time = from_time or datetime.datetime.utcnow()
        self.access_token = token['access_token']
        self.token_expiration = from_time + datetime.timedelta(seconds=token['expires_in'])

    def _get_access_token(self) -> str:
        return self.access_token

    def _access_token_invalid(self, from_time: datetime.datetime = None) -> bool:
        from_time = from_time or datetime.datetime.utcnow()
        return not self.access_token or self._token_expired(from_time)

    def _token_expired(self, from_time: datetime.datetime = None) -> bool:
        from_time = from_time or datetime.datetime.utcnow()
        return self.token_expiration < from_time

    def _invalid_client_secret_response(self, response) -> bool:
        return response.status_code in [400,401] and response.json()['error_description'] == 'Invalid client secret'

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
        return {"Authorization": f"Bearer {self._get_access_token()}"}

    def _refresh_credentials(self) -> bool:
        new_client_id, new_secret = self._get_updated_credentials()
        current_client_id, current_secret = self._get_credentials()
        if new_client_id != current_client_id or new_secret != current_secret:
            self.logger.info("Updated credentials found! Setting them as new api credentials")
            self._set_credentials(new_client_id, new_secret)
            return True
        self.logger.warning("No updated credentials were found")
        return False

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
            if self._invalid_client_secret_response(e.response):
                if self._refresh_credentials( ):
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

    def _set_credentials(self, client_id: str, secret: str) -> None:
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

    def get_user_by_username(self, realm_name, username) -> dict:
        self.logger.info(f"Getting user '{username}' from realm '{realm_name}'")
        endpoint = f"/admin/realms/navex/users"
        query_params = {'username':username}
        r = self._make_request('GET', endpoint, query_params)
        return r.json()

    def remove_user_by_id(self, realm_name: str, user_id: str):
        self.logger.info(f"Removing user '{user_id}' from realm '{realm_name}'")
        endpoint = f"/admin/realms/navex/users/{user_id}"
        r = self._make_request('DELETE', endpoint)
        r.raise_for_status()

    def remove_user_by_username(self, realm_name, username):
        user = self.get_user_by_username(realm_name, username)
        if user:
            self.logger.info(f"username '{username}' has kc user id '{user[0]['id']}'")
            self.remove_user_by_id(realm_name, user[0]['id'])
        else:
            self.logger.info(f"username '{username}' was not found in realm '{realm_name}''")

    def get_users_response(self, realm_name):
        self.logger.info(f"Getting users from realm '{realm_name}'")
        endpoint = f"/admin/realms/navex/users"
        r = self._make_request('GET', endpoint)
        return r
