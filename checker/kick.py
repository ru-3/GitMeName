"""
checker/kick.py
------------------
Kick does not currently publish an official, documented API
for checking username availability, so GitMeName falls back to
probing the public profile URL and applying smart HTTP-status +
page-content detection (see checker/url_checker.py).

Profile URL pattern:
    https://kick.com/{username}

All detection rules (status codes, "not found" phrases, headers,
timeout) are overridable in config.yaml under platforms.kick.*
"""

from __future__ import annotations

from checker.url_checker import GenericURLChecker


class KickChecker(GenericURLChecker):
    key = "kick"
    name = "Kick"
    color = "green3"
    profile_url = "https://kick.com/{username}"
