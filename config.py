"""
config.py
---------
Central configuration for GitMeName.

Load order (later overrides earlier):
    1. built-in defaults (below)
    2. config.yaml in the project root (if present)
    3. environment variables (for secrets / tokens)

Never commit real tokens to config.yaml — use environment variables
or a local, git-ignored config.yaml instead.

Every platform's profile URL and detection rules (status codes,
"not found" phrases, headers, timeout) can be overridden per-platform
under the `platforms:` key in config.yaml without touching any code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "config.yaml"
LOG_DIR = ROOT_DIR / "logs"
OUTPUT_DIR = ROOT_DIR / "output"

APP_NAME = "GitMeName"
APP_VERSION = "2.0.0"

# Default detection rules for URL-fallback platforms (no official API).
# `not_found_status`  -> username is AVAILABLE
# `found_status`       -> username is TAKEN (unless a not-found phrase matches)
# `ambiguous_status`   -> UNKNOWN (rate limited / bot-protected / blocked)
# `not_found_phrases`  -> body text (lower-cased) indicating AVAILABLE even on HTTP 200
_DEFAULT_URL_PLATFORMS: dict[str, dict[str, Any]] = {
    "tiktok": {
        "profile_url": "https://www.tiktok.com/@{username}",
        "not_found_status": [404],
        "found_status": [200],
        "ambiguous_status": [403, 429, 503],
        "not_found_phrases": [
            "couldn't find this account",
            "user not found",
            "page not available",
        ],
        "timeout": 12,
    },
    "instagram": {
        "profile_url": "https://www.instagram.com/{username}/",
        "not_found_status": [404],
        "found_status": [200],
        "ambiguous_status": [403, 429, 401],
        "not_found_phrases": [
            "sorry, this page isn't available",
            "page isn't available",
            "the link you followed may be broken",
        ],
        "timeout": 12,
    },
    "twitter": {
        "profile_url": "https://x.com/{username}",
        "not_found_status": [404],
        "found_status": [200],
        "ambiguous_status": [403, 429],
        "not_found_phrases": [
            "this account doesn't exist",
            "page doesn't exist",
        ],
        "timeout": 12,
    },
    "telegram": {
        "profile_url": "https://t.me/{username}",
        "not_found_status": [404],
        "found_status": [200],
        "ambiguous_status": [429],
        "not_found_phrases": [
            "if you have telegram, you can contact",
            "tgme_page_title\">telegram: contact",
            "we couldn't find this",
        ],
        "timeout": 10,
    },
    "snapchat": {
        "profile_url": "https://www.snapchat.com/add/{username}",
        "not_found_status": [404],
        "found_status": [200],
        "ambiguous_status": [403, 429],
        "not_found_phrases": [
            "sorry, we could not find",
            "content not found",
            "page not found",
        ],
        "timeout": 10,
    },
    "pinterest": {
        "profile_url": "https://www.pinterest.com/{username}/",
        "not_found_status": [404],
        "found_status": [200],
        "ambiguous_status": [403, 429],
        "not_found_phrases": [
            "page not found",
            "sorry! we couldn't find that page",
            "user not found",
        ],
        "timeout": 10,
    },
    "kick": {
        "profile_url": "https://kick.com/{username}",
        "not_found_status": [404],
        "found_status": [200],
        "ambiguous_status": [403, 429],
        "not_found_phrases": [
            "not found",
            "page could not be found",
        ],
        "timeout": 10,
    },
    "steam": {
        "profile_url": "https://steamcommunity.com/id/{username}",
        "not_found_status": [404],
        "found_status": [200],
        "ambiguous_status": [429],
        "not_found_phrases": [
            "the specified profile could not be found",
            "no user found",
        ],
        "timeout": 10,
    },
    "roblox": {
        "profile_url": "https://www.roblox.com/users/profile?username={username}",
        "not_found_status": [404],
        "found_status": [200],
        "ambiguous_status": [429],
        "not_found_phrases": [
            "page cannot be found",
            "user not found",
        ],
        "timeout": 10,
    },
}

DEFAULTS: dict[str, Any] = {
    "app": {
        "name": APP_NAME,
        "version": APP_VERSION,
    },
    "network": {
        "timeout_seconds": 10,
        "max_retries": 3,
        "retry_backoff_seconds": 1.5,
        "max_concurrent_requests": 25,
        "user_agent": f"GitMeName/{APP_VERSION} (+https://github.com/)",
    },
    "logging": {
        "level": "INFO",
        "file": "logs/gitmename.log",
        "max_bytes": 1_000_000,
        "backup_count": 3,
    },
    "output": {
        "directory": "output",
        "save_available": True,
    },
    "auth": {
        "github_token": "",
        "twitch_client_id": "",
        "twitch_client_secret": "",
    },
    "platforms": _DEFAULT_URL_PLATFORMS,
}


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
            return data
    return {}


@dataclass
class Config:
    """Resolved, ready-to-use configuration object."""

    app_name: str = APP_NAME
    app_version: str = APP_VERSION

    timeout_seconds: float = 10
    max_retries: int = 3
    retry_backoff_seconds: float = 1.5
    max_concurrent_requests: int = 25
    user_agent: str = f"GitMeName/{APP_VERSION}"

    log_level: str = "INFO"
    log_file: str = "logs/gitmename.log"
    log_max_bytes: int = 1_000_000
    log_backup_count: int = 3

    output_directory: str = "output"
    save_available: bool = True

    github_token: str = ""
    twitch_client_id: str = ""
    twitch_client_secret: str = ""

    platform_rules: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Config":
        merged = _deep_merge(DEFAULTS, _load_yaml_config())

        # Environment variables always win for secrets.
        github_token = os.environ.get("GITHUB_TOKEN", merged["auth"]["github_token"])
        twitch_id = os.environ.get("TWITCH_CLIENT_ID", merged["auth"]["twitch_client_id"])
        twitch_secret = os.environ.get(
            "TWITCH_CLIENT_SECRET", merged["auth"]["twitch_client_secret"]
        )

        return cls(
            app_name=merged["app"]["name"],
            app_version=merged["app"]["version"],
            timeout_seconds=merged["network"]["timeout_seconds"],
            max_retries=merged["network"]["max_retries"],
            retry_backoff_seconds=merged["network"]["retry_backoff_seconds"],
            max_concurrent_requests=merged["network"]["max_concurrent_requests"],
            user_agent=merged["network"]["user_agent"],
            log_level=merged["logging"]["level"],
            log_file=merged["logging"]["file"],
            log_max_bytes=merged["logging"]["max_bytes"],
            log_backup_count=merged["logging"]["backup_count"],
            output_directory=merged["output"]["directory"],
            save_available=merged["output"]["save_available"],
            github_token=github_token,
            twitch_client_id=twitch_id,
            twitch_client_secret=twitch_secret,
            platform_rules=merged["platforms"],
            raw=merged,
        )


def ensure_directories(cfg: Config) -> None:
    (ROOT_DIR / cfg.output_directory).mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / cfg.log_file).parent.mkdir(parents=True, exist_ok=True)
