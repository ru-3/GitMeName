"""
utils/http.py
--------------
Shared async HTTP helper used by every GitMeName platform checker.

Built on aiohttp and provides:
    - a single shared aiohttp.ClientSession (connection pooling via TCPConnector)
    - automatic retries with exponential backoff on transient errors
    - consistent, configurable timeout handling
    - a semaphore to cap global concurrency (be a good API/site citizen)
    - redirect-following GET requests, with the final resolved URL exposed
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from utils.logger import get_logger

log = get_logger()

# Errors worth retrying: network hiccups, timeouts. 4xx/5xx are handled
# by callers as normal (non-exceptional) responses, since a 404/403/429
# is meaningful signal for availability checking, not a transient fault.
_RETRYABLE_EXCEPTIONS = (
    aiohttp.ClientConnectorError,
    aiohttp.ServerDisconnectedError,
    aiohttp.ClientOSError,
    aiohttp.ClientPayloadError,
    asyncio.TimeoutError,
)


@dataclass
class Response:
    """Minimal, framework-agnostic response wrapper."""

    status_code: int
    text: str
    headers: dict = field(default_factory=dict)
    url: str = ""

    def json(self) -> Any:
        import json as _json

        return _json.loads(self.text)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code} for {self.url}")


class HttpClient:
    """Thin async wrapper around aiohttp.ClientSession with
    retry/timeout/concurrency limits and connection pooling."""

    def __init__(self, timeout: float, max_retries: int, backoff_seconds: float,
                 max_concurrent: int, user_agent: str):
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._max_retries = max(1, max_retries)
        self._backoff_seconds = backoff_seconds
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._headers = {"User-Agent": user_agent}
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "HttpClient":
        connector = aiohttp.TCPConnector(
            limit=self._max_concurrent,
            limit_per_host=max(4, self._max_concurrent // 2),
            ttl_dns_cache=300,
        )
        self._session = aiohttp.ClientSession(
            connector=connector,
            headers=self._headers,
            timeout=self._timeout,
            trust_env=True,
        )
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self._session:
            await self._session.close()

    async def request(self, method: str, url: str, *, headers: Optional[dict] = None,
                       params: Optional[dict] = None, allow_redirects: bool = True,
                       **kwargs: Any) -> Response:
        """Issue a request with retry + timeout + concurrency control."""
        assert self._session is not None, "HttpClient must be used as an async context manager"

        @retry(
            reraise=True,
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=self._backoff_seconds, min=1, max=20),
            retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        )
        async def _do_request() -> Response:
            async with self._semaphore:
                async with self._session.request(
                    method, url, headers=headers, params=params,
                    allow_redirects=allow_redirects, **kwargs,
                ) as resp:
                    body = await resp.text(errors="ignore")
                    return Response(
                        status_code=resp.status,
                        text=body,
                        headers=dict(resp.headers),
                        url=str(resp.url),
                    )

        try:
            return await _do_request()
        except _RETRYABLE_EXCEPTIONS as exc:
            log.warning("Request failed after retries: %s %s (%s)", method, url, exc)
            raise

    async def get(self, url: str, **kwargs: Any) -> Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Response:
        return await self.request("POST", url, **kwargs)
