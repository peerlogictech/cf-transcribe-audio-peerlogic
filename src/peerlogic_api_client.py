from datetime import datetime
import io
import logging
import os
from typing import (
    Callable,
    Dict,
)

from pydantic import BaseModel
import requests
import requests.compat
from urllib.parse import urljoin

from api_client import APIClient
from netsapiens_api_client import netsapiens_auth_token_from_response

log = logging.getLogger(__name__)


class NetsapiensAPICredentials(BaseModel):
    id: str
    created_at: datetime
    modified_by: str
    modified_at: datetime
    voip_provider: str
    api_url: str

    client_id: str
    client_secret: str
    username: str
    password: str
    active: bool


class PeerlogicAPIClient(APIClient):
    def __init__(self, peerlogic_api_url: str = None) -> None:
        # fallback to well-known environment variables
        if not peerlogic_api_url:
            peerlogic_api_url = os.getenv("PEERLOGIC_API_URL")

        super().__init__(peerlogic_api_url)

        # create base urls
        root_api_url = self.get_root_api_url()
        self._peerlogic_auth_url = urljoin(root_api_url, "login")
        self._peerlogic_netsapiens_api_credentials_url = urljoin(root_api_url, "integrations/netsapiens/admin/api-credentials")

    def get_auth_url(self) -> str:
        return self._peerlogic_auth_url

    def get_netsapiens_api_credentials_url(self) -> str:
        return self._peerlogic_netsapiens_api_credentials_url

    def get_session(self) -> requests.Session:
        s = self._session
        if not s:
            raise TypeError("Session is None. Must call the login() method before calling any other api accessor.")

        return s

    def login(self, username: str = None, password: str = None, request: Callable = requests.request) -> requests.Response:
        """
        Perform a login, grabbing an auth token.
        """
        try:
            # fallback to well-known environment variables
            if not username:
                username = os.getenv("PEERLOGIC_API_USERNAME")

            if not password:
                password = os.getenv("PEERLOGIC_API_PASSWORD")

            headers = {"Content-Type": "application/x-www-form-urlencoded"}  # explicitly set even though it's not necessary
            payload = {"username": username, "password": password}

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

    def get_netsapiens_api_credentials(self, voip_provider_id, session: requests.Session = None) -> NetsapiensAPICredentials:
        """
        Perform a login, grabbing an auth token.
        This works for both Netsapiens and peerlogic.
        """
        try:
            url = self._peerlogic_netsapiens_api_credentials_url
            log.info(f"Retrieving credentials for voip_provider_id='{voip_provider_id}' from url='{url}'")

            if not session:
                session = self.get_session()

            response = session.get(url, params={"voip_provider_id": voip_provider_id, "active": True})
            response.raise_for_status()

            data = response.json()
            credentials_count = data.get("count")
            credentials_list = data.get("results")
            if credentials_count == 0:
                raise Exception(f"No active credentials found for voip_provider_id='{voip_provider_id}' from url='{url}'")

            return NetsapiensAPICredentials(**credentials_list[0])
        except Exception as e:
            msg = f"Problem occurred retreiving credentials for voip_provider_id='{voip_provider_id}' from url='{url}'"
            log.exception(msg, e)
            raise Exception(msg)

    def get_call_partial_url(self, call_id: str, call_partial_id: str = None) -> str:
        """Returns url for a particular resource if call partial id is given, otherwise gives list/create endpoint"""
        if call_partial_id:  # url is for a particular resource
            return urljoin(self.get_root_api_url(), f"/api/calls/{call_id}/partials/{call_partial_id}/")
        return urljoin(self.get_root_api_url(), f"/api/calls/{call_id}/partials/")

    def get_call_audio_partial_url(self, call_id: str, call_partial_id: str, call_audio_partial_id: str = None) -> str:
        """Returns url for a particular resource if call audio partial id is given, otherwise gives list/create endpoint"""
        if call_audio_partial_id:  # url is for a particular resource
            return urljoin(self.get_root_api_url(), f"/api/calls/{call_id}/partials/{call_partial_id}/audio/{call_audio_partial_id}/")
        return urljoin(self.get_root_api_url(), f"/api/calls/{call_id}/partials/{call_partial_id}/audio/")

    def get_call_transcript_partial_url(self, call_id: str, call_partial_id: str, call_transcript_partial_id: str = None) -> str:
        """Returns url for a particular resource if call audio partial id is given, otherwise gives list/create endpoint"""
        if call_transcript_partial_id:  # url is for a particular resource
            return urljoin(self.get_root_api_url(), f"/api/calls/{call_id}/partials/{call_partial_id}/transcripts/{call_transcript_partial_id}/")
        return urljoin(self.get_root_api_url(), f"/api/calls/{call_id}/partials/{call_partial_id}/transcripts/")

    def get_call_audio_partial(self, call_id: str, call_partial_id: str, call_audio_partial_id: str, session: requests.Session = None) -> Dict:
        if not session:
            session = self.get_session()

        try:
            url = self.get_call_audio_partial_url(call_id, call_partial_id, call_audio_partial_id)
            response = session.get(url=url)
            response.raise_for_status()

            return response.json()
        except Exception as e:
            msg = f"Problem occurred getting an audio partial at '{url}'."
            log.exception(msg, e)
            raise Exception(msg)

    def get_call_audio_partial_wavfile(self, call_id: str, call_partial_id: str, call_audio_partial_id: str, session: requests.Session = None) -> bytes:
        if not session:
            session = self.get_session()

        call_audio_data = self.get_call_audio_partial(call_id, call_partial_id, call_audio_partial_id)
        url: str = call_audio_data.get("signed_url")

        try:
            response = requests.get(url=url)
            response.raise_for_status()

            return response.content
        except Exception as e:
            msg = f"Problem occurred getting wavefile for '{url}'."
            log.exception(msg, e)
            raise Exception(msg)

    def initialize_call_transcript_partial(
        self, call_id: str, call_partial_id: str, transcript_type: str, mime_type: str = "text/plain", session: requests.Session = None
    ) -> Dict:
        if not session:
            session = self.get_session()

        try:
            url = self.get_call_transcript_partial_url(call_id, call_partial_id)
            data = {"mime_type": mime_type, "call_partial": call_partial_id, "transcript_type": transcript_type}

            response = session.post(url=url, data=data)
            response.raise_for_status()

            return response.json()
        except Exception as e:
            msg = f"Problem occurred creating a new transcript partial for '{url}'"
            response_json = response.json()
            log.exception(f"{msg}. Response was {response_json}. Exception was {e}.")
            raise Exception(msg)

    def finalize_call_transcript_partial(
        self,
        id: str,
        call_id: str,
        call_partial_id: str,
        transcript_string: str,
        mime_type: str = "text/plain",
        session: requests.Session = None,
    ) -> Dict:
        if not session:
            session = self.get_session()

        file = io.StringIO(transcript_string)

        try:
            url = self.get_call_transcript_partial_url(call_id, call_partial_id, id)
            files = {mime_type: file}
            response = session.patch(url=url, files=files)
            response.raise_for_status()

            return response.json()
        except Exception as e:
            msg = f"Problem occurred finalizing the transcript partial for '{url}'."
            log.exception(msg, e)
            raise Exception(msg)


#
# Entrypoint
#

if __name__ == "__main__":
    """Only run when from command line / scripted."""
    # ensure environment variables are loaded
    from dotenv import load_dotenv

    load_dotenv()

    # create client and login
    peerlogic_api = PeerlogicAPIClient()
    peerlogic_api.login()
    print(peerlogic_api._auth_token.get_access_token())
