"""
checker/roblox.py
------------------
Roblox does not currently publish an official, documented API
for checking username availability, so GitMeName falls back to
probing the public profile URL and applying smart HTTP-status +
page-content detection (see checker/url_checker.py).

Profile URL pattern:
    https://www.roblox.com/users/profile?username={username}

All detection rules (status codes, "not found" phrases, headers,
timeout) are overridable in config.yaml under platforms.roblox.*
"""

from __future__ import annotations

from checker.url_checker import GenericURLChecker


class RobloxChecker(GenericURLChecker):
    key = "roblox"
    name = "Roblox"
    color = "red3"
    profile_url = "https://www.roblox.com/users/profile?username={username}"
