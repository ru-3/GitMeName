"""
checker/pinterest.py
------------------
Pinterest does not currently publish an official, documented API
for checking username availability, so GitMeName falls back to
probing the public profile URL and applying smart HTTP-status +
page-content detection (see checker/url_checker.py).

Profile URL pattern:
    https://www.pinterest.com/{username}/

All detection rules (status codes, "not found" phrases, headers,
timeout) are overridable in config.yaml under platforms.pinterest.*
"""

from __future__ import annotations

from checker.url_checker import GenericURLChecker


class PinterestChecker(GenericURLChecker):
    key = "pinterest"
    name = "Pinterest"
    color = "red1"
    profile_url = "https://www.pinterest.com/{username}/"
