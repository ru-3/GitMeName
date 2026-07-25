"""
checker/twitter.py
------------------
Twitter/X does not currently publish an official, documented API
for checking username availability, so GitMeName falls back to
probing the public profile URL and applying smart HTTP-status +
page-content detection (see checker/url_checker.py).

Profile URL pattern:
    https://x.com/{username}

All detection rules (status codes, "not found" phrases, headers,
timeout) are overridable in config.yaml under platforms.twitter.*
"""

from __future__ import annotations

from checker.url_checker import GenericURLChecker


class TwitterChecker(GenericURLChecker):
    key = "twitter"
    name = "Twitter/X"
    color = "dodger_blue1"
    profile_url = "https://x.com/{username}"
