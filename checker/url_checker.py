"""
checker/url_checker.py
-----------------------
Generic URL-based availability checker.

Used as the fallback strategy for any platform that does not expose
an official, documented username-availability API. Instead of an API
call, it requests the platform's public profile URL and infers
availability from:

    1. HTTP status code       (404 / 200 / 301 / 302 / 403 / 429 ...)
    2. Final redirected URL   (some sites 301/302 to a login or 404 page)
    3. Page content phrases   ("user not found", "page doesn't exist", ...)

Every platform subclass only needs to set class attributes (or, more
commonly, everything is driven by the `platforms.<key>` section of
config.yaml so no code changes are required to tune detection rules).

Returned status is always one of: AVAILABLE, TAKEN, UNKNOWN.
UNKNOWN covers network errors, rate limiting (429), and bot/CAPTCHA
protection (403 etc.) — cases where we genuinely can't tell.
"""

from __future__ import annotations

import time
from typing import Iterable

from checker.base import CheckResult, Method, PlatformChecker, Status
from utils.logger import log_check

DEFAULT_NOT_FOUND_STATUS = (404,)
DEFAULT_FOUND_STATUS = (200, 301, 302)
DEFAULT_AMBIGUOUS_STATUS = (403, 429, 405, 500, 502, 503)
DEFAULT_NOT_FOUND_PHRASES = (
    "user not found",
    "page not found",
    "doesn't exist",
    "does not exist",
    "couldn't find this account",
    "could not find this account",
    "page isn't available",
    "page not available",
    "profile could not be found",
    "no user found",
    "account removed",
    "content isn't available",
)


class GenericURLChecker(PlatformChecker):
    """Base class for every no-API, URL-probing platform checker."""

    key: str = "platform"
    method: str = Method.URL.value

    # Class-level defaults; usually overridden per-platform via config.yaml
    # under platforms.<key>.* — see config.py's _DEFAULT_URL_PLATFORMS.
    profile_url: str = ""
    not_found_status: Iterable[int] = DEFAULT_NOT_FOUND_STATUS
    found_status: Iterable[int] = DEFAULT_FOUND_STATUS
    ambiguous_status: Iterable[int] = DEFAULT_AMBIGUOUS_STATUS
    not_found_phrases: Iterable[str] = DEFAULT_NOT_FOUND_PHRASES
    extra_headers: dict = {}
    body_scan_limit: int = 40_000  # chars of body to scan for phrases

    def _rules(self) -> dict:
        return getattr(self.config, "platform_rules", {}).get(self.key, {})

    async def _check(self, username: str, http) -> CheckResult:
        rules = self._rules()
        url_template = rules.get("profile_url", self.profile_url)
        url = url_template.format(username=username)

        not_found_status = set(rules.get("not_found_status", self.not_found_status))
        found_status = set(rules.get("found_status", self.found_status))
        ambiguous_status = set(rules.get("ambiguous_status", self.ambiguous_status))
        phrases = [p.lower() for p in rules.get("not_found_phrases", self.not_found_phrases)]
        headers = {"Accept": "text/html,application/xhtml+xml", **self.extra_headers, **rules.get("headers", {})}

        start = time.monotonic()
        try:
            resp = await http.get(url, headers=headers, allow_redirects=True)
        except Exception as exc:  # noqa: BLE001 - surfaced as UNKNOWN, never crashes a batch
            elapsed = time.monotonic() - start
            log_check(self.name, username, self.method, "ERR", elapsed, "unknown")
            return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed,
                                f"network error: {exc}")

        elapsed = time.monotonic() - start
        status_code = resp.status_code
        body_lower = resp.text.lower()[: self.body_scan_limit]

        # 1. Ambiguous statuses (rate limiting / bot protection) -> UNKNOWN
        if status_code in ambiguous_status:
            log_check(self.name, username, self.method, status_code, elapsed, "unknown")
            reason = "rate limited" if status_code == 429 else "blocked/protected"
            return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed,
                                f"HTTP {status_code} ({reason})")

        # 2. Explicit not-found status codes -> AVAILABLE
        if status_code in not_found_status:
            log_check(self.name, username, self.method, status_code, elapsed, "available")
            return CheckResult(self.name, username, Status.AVAILABLE, self.method, elapsed,
                                f"HTTP {status_code}")

        # 3. Content-based detection, even on a 200 (many SPAs return 200 for
        #    a client-rendered "not found" page).
        if any(phrase in body_lower for phrase in phrases):
            log_check(self.name, username, self.method, status_code, elapsed, "available")
            return CheckResult(self.name, username, Status.AVAILABLE, self.method, elapsed,
                                "matched a 'not found' phrase in page content")

        # 4. Known "found" status codes with no not-found phrase -> TAKEN
        if status_code in found_status:
            log_check(self.name, username, self.method, status_code, elapsed, "taken")
            return CheckResult(self.name, username, Status.TAKEN, self.method, elapsed,
                                f"HTTP {status_code}")

        # 5. Anything else is unrecognized -> UNKNOWN, never guess.
        log_check(self.name, username, self.method, status_code, elapsed, "unknown")
        return CheckResult(self.name, username, Status.UNKNOWN, self.method, elapsed,
                            f"unrecognized HTTP {status_code}")
