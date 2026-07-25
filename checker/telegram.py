"""
checker/telegram.py
------------------
Telegram does not currently publish an official, documented API
for checking username availability, so GitMeName falls back to
probing the public profile URL and applying smart HTTP-status +
page-content detection (see checker/url_checker.py).

Profile URL pattern:
    https://t.me/{username}

All detection rules (status codes, "not found" phrases, headers,
timeout) are overridable in config.yaml under platforms.telegram.*
"""

from __future__ import annotations

from checker.url_checker import GenericURLChecker


class TelegramChecker(GenericURLChecker):
    key = "telegram"
    name = "Telegram"
    color = "sky_blue1"
    profile_url = "https://t.me/{username}"
