"""
checker/tiktok.py
------------------
TikTok does not currently publish an official, documented API
for checking username availability, so GitMeName falls back to
probing the public profile URL and applying smart HTTP-status +
page-content detection (see checker/url_checker.py).

Profile URL pattern:
    https://www.tiktok.com/@{username}

All detection rules (status codes, "not found" phrases, headers,
timeout) are overridable in config.yaml under platforms.tiktok.*
"""

from __future__ import annotations

from checker.url_checker import GenericURLChecker


class TikTokChecker(GenericURLChecker):
    key = "tiktok"
    name = "TikTok"
    color = "bright_cyan"
    profile_url = "https://www.tiktok.com/@{username}"
