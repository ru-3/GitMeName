"""
checker/reddit.py
------------------
Reddit username availability via Reddit's own official, documented
endpoint (the same one reddit.com's signup form calls):
    GET https://www.reddit.com/api/username_available.json?user={username}

Returns a bare JSON boolean: true (available) or false (taken).
Docs: https://www.reddit.com/dev/api/#GET_api_username_available
"""

from __future__ import annotations

import time

from checker.base import CheckResult, Method, PlatformChecker, Status
from utils.logger import log_check

API_URL = "https://www.reddit.com/api/username_available.json"


class RedditChecker(PlatformChecker):
    key = "reddit"
    name = "Reddit"
    color = "dark_orange"
    method = Method.API.value

    async def _check(self, username: str, http) -> CheckResult:
        start = time.monotonic()
        try:
            resp = await http.get(API_URL, params={"user": username})
        except Exception as exc:  # noqa: BLE001
            elapsed = time.monotonic() - start
            log_check(self.name, username, self.method, "ERR", elapsed, "unknown")
            return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed, str(exc))

        elapsed = time.monotonic() - start
        code = resp.status_code

        if code != 200:
            log_check(self.name, username, self.method, code, elapsed, "unknown")
            return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed, f"HTTP {code}")

        try:
            data = resp.json()
        except ValueError:
            log_check(self.name, username, self.method, code, elapsed, "unknown")
            return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed,
                                "unexpected response body")

        if isinstance(data, bool):
            status = Status.AVAILABLE if data else Status.TAKEN
            log_check(self.name, username, self.method, code, elapsed, status.value)
            return CheckResult(self.name, username, status, self.method, elapsed)

        if isinstance(data, dict):
            log_check(self.name, username, self.method, code, elapsed, "unknown")
            return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed,
                                str(data.get("explanation", data)))

        log_check(self.name, username, self.method, code, elapsed, "unknown")
        return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed, "unrecognized response")
