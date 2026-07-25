"""
checker/steam.py
------------------
Steam does not currently publish an official, documented API
for checking username availability, so GitMeName falls back to
probing the public profile URL and applying smart HTTP-status +
page-content detection (see checker/url_checker.py).

Profile URL pattern:
    https://steamcommunity.com/id/{username}

All detection rules (status codes, "not found" phrases, headers,
timeout) are overridable in config.yaml under platforms.steam.*
"""

from __future__ import annotations

from checker.url_checker import GenericURLChecker


class SteamChecker(GenericURLChecker):
    key = "steam"
    name = "Steam"
    color = "deep_sky_blue4"
    profile_url = "https://steamcommunity.com/id/{username}"
