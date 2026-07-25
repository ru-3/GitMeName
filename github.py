"""
checker/github.py
------------------
GitHub username availability via the official REST API:
    GET https://api.github.com/users/{username}

    404 -> available
    200 -> taken
    other -> unknown

Supports an optional Personal Access Token (no special scopes needed
for this read-only lookup) which raises the rate limit from 60 to
5000 requests/hour. Docs: https://docs.github.com/en/rest/users/users
"""

from __future__ import annotations

import time

from checker.base import CheckResult, Method, PlatformChecker, Status
from utils.logger import log_check

API_URL = "https://api.github.com/users/{username}"


class GitHubChecker(PlatformChecker):
    key = "github"
    name = "GitHub"
    color = "grey93"
    method = Method.API.value

    async def _check(self, username: str, http) -> CheckResult:
        headers = {"Accept": "application/vnd.github+json"}
        if self.config.github_token:
            headers["Authorization"] = f"Bearer {self.config.github_token}"

        start = time.monotonic()
        try:
            resp = await http.get(API_URL.format(username=username), headers=headers)
        except Exception as exc:  # noqa: BLE001
            elapsed = time.monotonic() - start
            log_check(self.name, username, self.method, "ERR", elapsed, "unknown")
            return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed, str(exc))

        elapsed = time.monotonic() - start
        code = resp.status_code

        if code == 404:
            log_check(self.name, username, self.method, code, elapsed, "available")
            return CheckResult(self.name, username, Status.AVAILABLE, self.method, elapsed)
        if code == 200:
            log_check(self.name, username, self.method, code, elapsed, "taken")
            return CheckResult(self.name, username, Status.TAKEN, self.method, elapsed)
        if code in (403, 429):
            detail = "rate limited (add a GitHub token)"
            remaining = resp.headers.get("x-ratelimit-remaining") if hasattr(resp, "headers") else None
            reset = resp.headers.get("x-ratelimit-reset") if hasattr(resp, "headers") else None
            if remaining == "0" and reset:
                try:
                    wait_s = max(0, int(reset) - int(time.time()))
                    detail = f"rate limited (add a GitHub token) — resets in ~{wait_s}s"
                except ValueError:
                    pass
            log_check(self.name, username, self.method, code, elapsed, "unknown")
            return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed, detail)

        log_check(self.name, username, self.method, code, elapsed, "unknown")
        return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed, f"HTTP {code}")
