"""
checker/twitch.py
------------------
Twitch username ("login") availability via the official Helix API:
    GET https://api.twitch.tv/helix/users?login={username}

An empty `data` array means no user owns that login (available).
Requires an app access token obtained via the official OAuth Client
Credentials flow:
    POST https://id.twitch.tv/oauth2/token

Docs:
    https://dev.twitch.tv/docs/api/reference/#get-users
    https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#client-credentials-grant-flow

Requires TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET (config.yaml or env vars).
Create an app at https://dev.twitch.tv/console/apps to obtain these.
"""

from __future__ import annotations

import time

from checker.base import CheckResult, Method, PlatformChecker, Status
from utils.logger import log_check

TOKEN_URL = "https://id.twitch.tv/oauth2/token"
USERS_URL = "https://api.twitch.tv/helix/users"


class TwitchChecker(PlatformChecker):
    key = "twitch"
    name = "Twitch"
    color = "medium_purple1"
    method = Method.API.value

    def __init__(self, config):
        super().__init__(config)
        self._access_token: str | None = None
        self._token_expiry: float = 0.0

    @property
    def _has_credentials(self) -> bool:
        return bool(self.config.twitch_client_id and self.config.twitch_client_secret)

    async def _get_app_token(self, http) -> str:
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        resp = await http.post(
            TOKEN_URL,
            params={
                "client_id": self.config.twitch_client_id,
                "client_secret": self.config.twitch_client_secret,
                "grant_type": "client_credentials",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600) - 60
        return self._access_token

    async def _check(self, username: str, http) -> CheckResult:
        start = time.monotonic()
        if not self._has_credentials:
            elapsed = time.monotonic() - start
            log_check(self.name, username, self.method, "N/A", elapsed, "unknown")
            return CheckResult(
                self.name, username, Status.UNKNOWN, self.method, elapsed,
                "Twitch credentials not configured (set TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET)",
            )

        try:
            token = await self._get_app_token(http)
            resp = await http.get(
                USERS_URL,
                params={"login": username},
                headers={
                    "Client-Id": self.config.twitch_client_id,
                    "Authorization": f"Bearer {token}",
                },
            )
        except Exception as exc:  # noqa: BLE001
            elapsed = time.monotonic() - start
            log_check(self.name, username, self.method, "ERR", elapsed, "unknown")
            return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed, str(exc))

        elapsed = time.monotonic() - start
        code = resp.status_code
        if code != 200:
            log_check(self.name, username, self.method, code, elapsed, "unknown")
            return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed, f"HTTP {code}")

        data = resp.json().get("data", [])
        status = Status.TAKEN if data else Status.AVAILABLE
        log_check(self.name, username, self.method, code, elapsed, status.value)
        return CheckResult(self.name, username, status, self.method, elapsed)
