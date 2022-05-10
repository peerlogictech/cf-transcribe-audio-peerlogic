import logging
import requests
import requests.compat
from typing import (
    Callable,
    Dict,
    Optional,
)

from urllib.parse import urljoin
from urllib3.response import HTTPResponse

from api_client import APIClient

log = logging.getLogger(__name__)


class NetsapiensAuthToken(dict):
    # Expected format as of 2021-12-10
    # {
    #     "access_token": "thisisanalphanumericbearertoken",  # REQUIRED VALUE
    #     "apiversion": "Version: 41.2.3",
    #     "client_id": "peerlogic-ml-rest-api-ENV",
    #     "displayName": "USER NAME",
    #     "domain": "Peerlogic",
    #     "expires_at": 1639084657,
    #     "expires_in": 3600,
    #     "refresh_token": "thisisanalphanumericrefreshtoken",
    #     "scope": "Super User",
    #     "scoped_domains": [
    #         "Peerlogic"
    #     ],
    #     "territory": "Peerlogic",
    #     "token_type": "Bearer",
    #     "uid": "1234@Peerlogic",
    #     "user": "1234",
    #     "user_email": "systemuser@peerlogic.com",
    #     "username": "1234@Peerlogic"
    # }

    def __init__(self, auth_token_dict: Dict) -> None:
        self.update(auth_token_dict)

    def get_access_token(self) -> Optional[str]:
        return self.get("access_token")

    def get_refresh_token(self) -> Optional[str]:
        return self.get("refresh_token")


def netsapiens_auth_token_from_response(auth_response: requests.Response) -> NetsapiensAuthToken:
    return NetsapiensAuthToken(auth_response.json())


class NetsapiensAPIClient(APIClient):
    def __init__(self, root_api_url: str) -> None:
        log.info("NetsapiensAPIClient  init")
        log.info(root_api_url)
        super().__init__(root_api_url=root_api_url)

        # create base urls
        root_api_url = self.get_root_api_url()
        self._netsapiens_auth_url = urljoin(root_api_url, "oauth2/token/")

    def get_auth_url(self) -> str:
        return self._netsapiens_auth_url

    def get_session(self) -> requests.Session:
        s = self._session
        if not s:
            raise TypeError("Session is None. Must call the login() method before calling any other api accessor.")

        return s

    def login(self, username: str, password: str, client_id: str, client_secret: str, request: Callable = requests.request) -> requests.Response:
        """
        Perform a login, grabbing an auth token.
        """
        try:
            headers = {"Content-Type": "application/x-www-form-urlencoded"}  # explicitly set even though it's not necessary
            payload = {
                "username": username,
                "password": password,
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "password",
                "format": "json",
            }

            url = self.get_auth_url()
            log.info(f"Authing into url='{url}' as username: '{username}'")
            auth_response = request("POST", url, headers=headers, data=payload)
            auth_response.raise_for_status()

            # parse response
            self._auth_token = netsapiens_auth_token_from_response(auth_response)

            # Session and Authorization header construction
            access_token = self._auth_token.get_access_token()
            self._session = requests.Session()
            self._session.headers.update({"Authorization": f"Bearer {access_token}"})

            return auth_response
        except Exception as e:
            msg = f"Problem occurred authenticating to url '{url}'."
            log.exception(msg, e)
            raise Exception(msg)

    def get_recording_urls(self, orig_callid: str, term_callid: str, session: requests.Session = None) -> Dict:
        if not session:
            session = self.get_session()

        try:
            params = {"object": "recording", "action": "read", "format": "json", "limit": 20, "orig_callid": orig_callid, "term_callid": term_callid}
            url = self.get_root_api_url()

            response = session.get(url=url, params=params)
            response.raise_for_status()

            return response.json()
        except Exception as e:
            msg = f"Problem occurred extracting from url '{url}'."
            log.exception(msg, e)
            raise Exception(msg)

    def get_recording_file(self, url: str, session: requests.Session = None) -> HTTPResponse:
        if not session:
            session = self.get_session()

        try:
            response = session.get(url, stream=True)
            response.raise_for_status()

            return response.raw
        except Exception as e:
            msg = f"Problem occurred downloading recording from url '{url}'."
            log.exception(msg, e)
            raise Exception(msg)
