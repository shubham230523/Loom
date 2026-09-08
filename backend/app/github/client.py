import httpx
import time
from typing import Dict, Any, Optional, Union
from backend.app.config import settings
from backend.app.api.errors import LoomError, RateLimitError, AuthenticationError
from backend.app.utils.logging import logger

class GitHubClient:
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.base_url = settings.GITHUB_API_URL
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Loom-API"
        }
        if access_token:
            self.headers["Authorization"] = f"Bearer {access_token}"

        self.timeout = 15.0

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"

        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data
                )

                self._handle_rate_limit(response)

                if response.status_code >= 400:
                    self._handle_error(response)

                return response.json() if response.content else None

            except httpx.TimeoutException:
                logger.error(f"GitHub API timeout: {method} {path}")
                raise LoomError("GitHub API request timed out", status_code=504)
            except httpx.RequestError as e:
                logger.error(f"GitHub API request error: {str(e)}")
                raise LoomError(f"GitHub API request failed: {str(e)}", status_code=502)

    def _handle_rate_limit(self, response: httpx.Response):
        remaining = response.headers.get("X-RateLimit-Remaining")
        limit = response.headers.get("X-RateLimit-Limit")
        reset_at = response.headers.get("X-RateLimit-Reset")

        if remaining is not None:
            logger.debug(f"GitHub Rate Limit: {remaining}/{limit}, resets at {reset_at}")

            if int(remaining) == 0:
                reset_time = int(reset_at) if reset_at else int(time.time() + 60)
                wait_seconds = max(0, reset_time - int(time.time()))

                raise RateLimitError(
                    message="GitHub API rate limit exceeded",
                    details={
                        "limit": limit,
                        "reset_at": reset_at,
                        "retry_after_seconds": wait_seconds
                    }
                )

    def _handle_error(self, response: httpx.Response):
        status_code = response.status_code
        try:
            error_data = response.json()
            message = error_data.get("message", "Unknown GitHub Error")
            details = error_data.get("errors")
        except Exception:
            message = response.text or "Unknown GitHub Error"
            details = None

        logger.error(f"GitHub API Error {status_code}: {message}")

        if status_code == 401:
            raise AuthenticationError("GitHub authentication failed or token expired")

        if status_code == 403 and "rate limit" in message.lower():
            raise RateLimitError(message="GitHub rate limit exceeded")

        raise LoomError(
            message=f"GitHub API Error: {message}",
            status_code=status_code,
            code="GITHUB_API_ERROR",
            details=details
        )

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, json_data: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request("POST", path, json_data=json_data)

    async def put(self, path: str, json_data: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request("PUT", path, json_data=json_data)

    async def patch(self, path: str, json_data: Optional[Dict[str, Any]] = None) -> Any:
        return await self.request("PATCH", path, json_data=json_data)

    async def delete(self, path: str) -> Any:
        return await self.request("DELETE", path)
