import logging

log = logging.getLogger(__name__)


class APIClient(object):
    def __init__(self, root_api_url: str = None) -> None:
        self._session = None

        # normalize the base_url
        self._root_api_url = root_api_url if root_api_url and root_api_url.endswith("/") else f"{root_api_url}/"
        log.debug(f"Initialized API Client. root_api_url: '{self._root_api_url}'")

    def get_root_api_url(self) -> str:
        return self._root_api_url
