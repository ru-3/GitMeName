"""
generator.py
------------
Generates candidate usernames according to a chosen mode:

    3          -> exactly 3 characters, letters/digits, no separator
    4          -> exactly 4 characters, letters/digits, no separator
    near_3     -> 3-character "core" but may include one separator
                  character stylistically inserted (e.g. "a-b7")
    near_4     -> same idea with a 4-character core
    custom     -> user supplies charset + length range

A separator (".", "-", "_", or none) can optionally be inserted into
"near" modes for stylistic variety. Separators are never inserted for
platforms/modes where it wouldn't make sense — the caller decides
whether to keep or strip them per-platform (some platforms disallow
certain separator characters in usernames).
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass
from enum import Enum
from typing import Optional

LETTERS = string.ascii_lowercase
DIGITS = string.digits


class UsernameType(str, Enum):
    THREE_CHAR = "3"
    FOUR_CHAR = "4"
    NEAR_THREE = "near_3"
    NEAR_FOUR = "near_4"
    CUSTOM = "custom"


class Separator(str, Enum):
    DOT = "."
    DASH = "-"
    UNDERSCORE = "_"
    NONE = ""


@dataclass
class GeneratorOptions:
    username_type: UsernameType
    separator: Separator = Separator.NONE
    count: int = 50
    # Only used when username_type == CUSTOM
    custom_length: int = 5
    custom_charset: str = LETTERS + DIGITS


def _random_core(length: int, charset: str = LETTERS + DIGITS) -> str:
    return "".join(random.choices(charset, k=length))


def _maybe_insert_separator(core: str, separator: Separator) -> str:
    if separator == Separator.NONE or len(core) < 2:
        return core
    pos = random.randint(1, len(core) - 1)
    return core[:pos] + separator.value + core[pos:]


def generate_one(options: GeneratorOptions) -> str:
    """Generate a single candidate username according to the given options."""
    if options.username_type == UsernameType.THREE_CHAR:
        return _random_core(3)

    if options.username_type == UsernameType.FOUR_CHAR:
        return _random_core(4)

    if options.username_type == UsernameType.NEAR_THREE:
        core = _random_core(3)
        return _maybe_insert_separator(core, options.separator)

    if options.username_type == UsernameType.NEAR_FOUR:
        core = _random_core(4)
        return _maybe_insert_separator(core, options.separator)

    if options.username_type == UsernameType.CUSTOM:
        core = _random_core(options.custom_length, options.custom_charset)
        return _maybe_insert_separator(core, options.separator)

    raise ValueError(f"Unknown username type: {options.username_type}")


def generate_batch(options: GeneratorOptions, exclude: Optional[set[str]] = None) -> list[str]:
    """Generate `options.count` unique usernames not already in `exclude`."""
    exclude = exclude or set()
    result: set[str] = set()
    # Safety cap so we never spin forever if the search space is exhausted.
    max_attempts = options.count * 50 + 100

    attempts = 0
    while len(result) < options.count and attempts < max_attempts:
        candidate = generate_one(options)
        attempts += 1
        if candidate not in exclude and candidate not in result:
            result.add(candidate)

    return list(result)
