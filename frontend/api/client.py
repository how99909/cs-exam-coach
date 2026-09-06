from typing import Any

import requests

from config import API_BASE_URL, DEFAULT_API_TIMEOUT


class ApiClient:
    def __init__(
        self,
        access_token: str | None = None,
    ):
        self.base_url = API_BASE_URL.rstrip("/")
        self.access_token = access_token
        
    def _headers(
        self,
        headers: dict[str, str] | None = None,
    ) -> dict[str, str]:
        result = dict(headers or {})
        
        if self.access_token:
            result["Authorization"] = f"Bearer {self.access_token}"
            
        return result
    
    def request(
        self,
        method: str,
        path: str,
        *,
        timeout: int = DEFAULT_API_TIMEOUT,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        return requests.request(
            method=method,
            url=f"{self.base_url}{path}",
            headers=self._headers(headers),
            timeout=timeout,
            **kwargs,
        )
        
    def get(
        self,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        return self.request(
            "GET",
            path,
            **kwargs,
        )
        
    def post(
        self,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        return self.request(
            "POST",
            path,
            **kwargs,
        )
        
    def patch(
        self,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        return self.request(
            "PATCH",
            path,
            **kwargs,
        )
        
    def delete(
        self,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        return self.request(
            "DELETE",
            path,
            **kwargs,
        )