"""
checker/registry.py
--------------------
Central registry of every platform checker GitMeName supports, in
menu order. API-backed checkers are listed first, followed by
URL-fallback checkers.
"""

from __future__ import annotations

from checker.github import GitHubChecker
from checker.reddit import RedditChecker
from checker.twitch import TwitchChecker
from checker.tiktok import TikTokChecker
from checker.instagram import InstagramChecker
from checker.twitter import TwitterChecker
from checker.telegram import TelegramChecker
from checker.snapchat import SnapchatChecker
from checker.pinterest import PinterestChecker
from checker.kick import KickChecker
from checker.steam import SteamChecker
from checker.roblox import RobloxChecker

PLATFORM_CHECKERS = {
    "github": GitHubChecker,
    "reddit": RedditChecker,
    "twitch": TwitchChecker,
    "tiktok": TikTokChecker,
    "instagram": InstagramChecker,
    "twitter": TwitterChecker,
    "telegram": TelegramChecker,
    "snapchat": SnapchatChecker,
    "pinterest": PinterestChecker,
    "kick": KickChecker,
    "steam": SteamChecker,
    "roblox": RobloxChecker,
}
