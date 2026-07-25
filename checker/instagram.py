"""
checker/instagram.py
------------------
Instagram does not currently publish an official, documented API
for checking username availability, so GitMeName falls back to
probing the public profile URL and applying smart HTTP-status +
page-content detection (see checker/url_checker.py).

Profile URL pattern:
    https://www.instagram.com/{username}/

All detection rules (status codes, "not found" phrases, headers,
timeout) are overridable in config.yaml under platforms.instagram.*
"""

from __future__ import annotations

from checker.url_checker import GenericURLChecker


class InstagramChecker(GenericURLChecker):
    key = "instagram"
    name = "Instagram"
    color = "medium_purple3"
    profile_url = "https://www.instagram.com/{username}/"
