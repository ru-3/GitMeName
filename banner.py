"""
banner.py
---------
GitMeName's ASCII art logo and startup version banner, rendered with
Rich styling and centered in the terminal.
"""

from __future__ import annotations

from rich.align import Align
from rich.console import Console, Group
from rich.text import Text

APP_VERSION = "2.0.0"

# Hand-built block-letter ASCII logo, guaranteed monospace alignment
# (no external figlet font dependency required).
LOGO_LINES = [
    "  ██   ██████ ██████ █    █ ██████ █    █   ██   █    █ ██████ ",
    " █  █    ██     ██   ██  ██ █      ██   █  █  █  ██  ██ █      ",
    " █       ██     ██   █ ██ █ █████  █ █  █ █    █ █ ██ █ █████  ",
    " █ ██    ██     ██   █    █ █      █  █ █ ██████ █    █ █      ",
    " █  █    ██     ██   █    █ █      █   ██ █    █ █    █ █      ",
    "  ██   ██████   ██   █    █ ██████ █    █ █    █ █    █ ██████ ",
]


def render_banner(console: Console) -> None:
    """Print the centered, colored GitMeName startup banner."""
    logo = Text()
    for i, line in enumerate(LOGO_LINES):
        # Subtle top-to-bottom shading from bright white to grey.
        style = ["bold bright_white", "bold bright_white", "bold grey93",
                 "bold grey93", "bold grey70", "bold grey70"][i % 6]
        logo.append(line + "\n", style=style)

    tagline = Text("The username-availability CLI\n", style="bold cyan", justify="center")
    subtitle = Text(
        f"v{APP_VERSION} · official API when available · smart URL fallback\n",
        style="dim italic",
        justify="center",
    )
    rule = Text("─" * 68, style="grey42")

    group = Group(
        Align.center(logo),
        Align.center(rule),
        Align.center(tagline),
        Align.center(subtitle),
    )
    console.print(group)
