"""
checker/base.py
----------------
Common types shared by every platform checker module in GitMeName.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Status(str, Enum):
    AVAILABLE = "available"
    TAKEN = "taken"
    UNKNOWN = "unknown"   # network error, protection/CAPTCHA, rate limit, etc.


class Method(str, Enum):
    API = "API"
    URL = "URL"


@dataclass
class CheckResult:
    platform: str
    username: str
    status: Status
    method: str = Method.URL.value
    response_time: float = 0.0     # seconds
    detail: str = ""


class PlatformChecker:
    """Base class every platform module implements.

    Subclasses are either:
      * API-backed  (github.py, reddit.py, twitch.py) -> method = "API"
      * URL-backed  (checker/url_checker.py subclasses) -> method = "URL"
    """

    key: str = "platform"
    name: str = "Platform"
    color: str = "white"          # Rich color/style name used in the UI
    method: str = Method.URL.value

    def __init__(self, config):
        self.config = config

    async def check(self, username: str, http) -> CheckResult:
        return await self._check(username, http)

    async def _check(self, username: str, http) -> CheckResult:
        raise NotImplementedError
