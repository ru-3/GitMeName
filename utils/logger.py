"""
utils/logger.py
----------------
Automatic, rotating file logging for GitMeName, plus a quiet console
logger. The Rich UI handles all interactive console output separately,
so the console handler here is deliberately minimal (warnings and
above) to avoid clobbering the live display.

Every check is logged with: timestamp, platform, username, method
(API/URL), response code (when applicable), response time, and the
final result — see `log_check()`.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_CONFIGURED = False
LOGGER_NAME = "gitmename"


def setup_logging(log_file: str, level: str = "INFO", max_bytes: int = 1_000_000,
                   backup_count: int = 3) -> logging.Logger:
    global _CONFIGURED
    logger = logging.getLogger(LOGGER_NAME)

    if _CONFIGURED:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Keep the console quiet — Rich owns the interactive display.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(console_handler)

    _CONFIGURED = True
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def log_check(platform: str, username: str, method: str, status_code: "int | str",
              response_time: float, result: str) -> None:
    """Structured, single-line log entry for one username check."""
    get_logger().info(
        "platform=%s username=%s method=%s response_code=%s response_time=%.3fs result=%s",
        platform, username, method, status_code, response_time, result,
    )
