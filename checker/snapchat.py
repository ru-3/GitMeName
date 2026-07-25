"""
checker/snapchat.py
------------------
Snapchat does not currently publish an official, documented API
for checking username availability, so GitMeName falls back to
probing the public profile URL and applying smart HTTP-status +
page-content detection (see checker/url_checker.py).

Profile URL pattern:
    https://www.snapchat.com/add/{username}

All detection rules (status codes, "not found" phrases, headers,
timeout) are overridable in config.yaml under platforms.snapchat.*
"""

from __future__ import annotations

from checker.url_checker import GenericURLChecker


class SnapchatChecker(GenericURLChecker):
    key = "snapchat"
    name = "Snapchat"
    color = "yellow1"
    profile_url = "https://www.snapchat.com/add/{username}"
