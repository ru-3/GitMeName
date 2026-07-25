#!/usr/bin/env python3
"""
main.py
-------
GitMeName — a production-ready username availability checker CLI.

Uses official platform APIs where available (GitHub, Reddit, Twitch)
and falls back to smart URL probing + content detection for every
other supported platform. Fully async, with connection pooling,
retries, live progress, and a Rich terminal UI.

Run:
    python main.py
"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from banner import render_banner
from checker.base import CheckResult, Method, Status
from checker.registry import PLATFORM_CHECKERS
from config import Config, ensure_directories
from generator import GeneratorOptions, Separator, UsernameType, generate_batch
from utils.http import HttpClient
from utils.logger import get_logger, setup_logging
from utils.stats import Stats

console = Console()

STATUS_STYLES = {
    Status.AVAILABLE: "bold green",
    Status.TAKEN: "red",
    Status.UNKNOWN: "yellow",
}

STATUS_LABELS = {
    Status.AVAILABLE: "AVAILABLE",
    Status.TAKEN: "TAKEN",
    Status.UNKNOWN: "UNKNOWN",
}

METHOD_STYLES = {
    Method.API.value: "bold cyan",
    Method.URL.value: "bold magenta",
}


def clear_screen() -> None:
    """Clear the terminal the same way on every startup."""
    sys.stdout.write("\033c")
    sys.stdout.flush()


def show_banner() -> None:
    render_banner(console)


def choose_platform() -> str:
    table = Table(title="Supported Platforms", show_lines=False)
    table.add_column("#", justify="right", style="bold white")
    table.add_column("Platform")
    table.add_column("Method")

    keys = list(PLATFORM_CHECKERS.keys())
    for i, key in enumerate(keys, start=1):
        checker_cls = PLATFORM_CHECKERS[key]
        label = f"[{checker_cls.color}]{checker_cls.name}[/{checker_cls.color}]"
        method_style = METHOD_STYLES.get(checker_cls.method, "white")
        method_label = f"[{method_style}]{checker_cls.method}[/{method_style}]"
        table.add_row(str(i), label, method_label)

    console.print(table)
    choice = IntPrompt.ask(
        "Select a platform by number", choices=[str(i) for i in range(1, len(keys) + 1)]
    )
    return keys[choice - 1]


def choose_generator_options() -> GeneratorOptions:
    console.print(
        Panel.fit(
            "[bold]3[/bold] = exactly 3 chars   [bold]4[/bold] = exactly 4 chars\n"
            "[bold]near_3[/bold] / [bold]near_4[/bold] = same core length, optional separator\n"
            "[bold]custom[/bold] = choose your own length/charset",
            title="Username Types",
        )
    )
    type_choice = Prompt.ask(
        "Username type",
        choices=["3", "4", "near_3", "near_4", "custom"],
        default="near_3",
    )
    username_type = UsernameType(type_choice)

    separator = Separator.NONE
    if username_type in (UsernameType.NEAR_THREE, UsernameType.NEAR_FOUR, UsernameType.CUSTOM):
        sep_choice = Prompt.ask(
            "Separator", choices=[".", "-", "_", "none"], default="none"
        )
        separator = Separator.NONE if sep_choice == "none" else Separator(sep_choice)

    custom_length = 5
    custom_charset = "abcdefghijklmnopqrstuvwxyz0123456789"
    if username_type == UsernameType.CUSTOM:
        custom_length = IntPrompt.ask("Custom length", default=5)
        custom_charset = Prompt.ask(
            "Custom charset (characters allowed)", default=custom_charset
        )

    count = IntPrompt.ask("How many usernames to generate/check?", default=50)

    return GeneratorOptions(
        username_type=username_type,
        separator=separator,
        count=count,
        custom_length=custom_length,
        custom_charset=custom_charset,
    )


def build_stats_table(stats: Stats, platform_name: str, platform_color: str) -> Table:
    table = Table(title=f"Live Statistics — [{platform_color}]{platform_name}[/{platform_color}]")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Total Checked", str(stats.total_checked))
    table.add_row("Available", f"[bold green]{stats.available}[/bold green]")
    table.add_row("Taken", f"[red]{stats.taken}[/red]")
    table.add_row("Unknown", f"[yellow]{stats.unknown}[/yellow]")
    table.add_row("Requests/sec", f"{stats.requests_per_second:.2f}")
    table.add_row("Elapsed Time", f"{stats.elapsed_seconds:.1f}s")
    return table


def _is_rate_limited(detail: str) -> bool:
    d = (detail or "").lower()
    return "rate limit" in d


async def run_checks(platform_key: str, usernames: list[str], config: Config) -> list[CheckResult]:
    checker_cls = PLATFORM_CHECKERS[platform_key]
    checker = checker_cls(config)
    stats = Stats()
    results: list[CheckResult] = []
    log = get_logger()

    # Once we've seen a handful of consecutive rate-limit responses, stop
    # burning further requests — they'll almost certainly fail the same
    # way for the rest of this run (e.g. GitHub's 60/hour anonymous cap).
    rate_limit_hits = 0
    RATE_LIMIT_ABORT_THRESHOLD = 3
    aborted = asyncio.Event()

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    )
    task_id = progress.add_task(f"Checking {checker.name}...", total=len(usernames))

    async def worker(name: str, http: HttpClient) -> None:
        nonlocal rate_limit_hits

        if aborted.is_set():
            result = CheckResult(
                checker.name, name, Status.UNKNOWN, checker.method, 0.0,
                "skipped (rate limit hit earlier in this batch)",
            )
        else:
            result = await checker.check(name, http)
            if result.status == Status.UNKNOWN and _is_rate_limited(result.detail):
                rate_limit_hits += 1
                if rate_limit_hits >= RATE_LIMIT_ABORT_THRESHOLD:
                    aborted.set()

        results.append(result)
        await stats.record(result.status.value)
        progress.advance(task_id)

    async with HttpClient(
        timeout=config.timeout_seconds,
        max_retries=config.max_retries,
        backoff_seconds=config.retry_backoff_seconds,
        max_concurrent=config.max_concurrent_requests,
        user_agent=config.user_agent,
    ) as http:
        with Live(console=console, refresh_per_second=4) as live:
            async def refresher() -> None:
                while not progress.finished:
                    live.update(build_group(progress, stats, checker.name, checker.color))
                    await asyncio.sleep(0.25)

            refresh_task = asyncio.create_task(refresher())
            await asyncio.gather(*(worker(name, http) for name in usernames))
            progress.stop_task(task_id)
            refresh_task.cancel()
            try:
                await refresh_task
            except asyncio.CancelledError:
                pass
            # Deterministic final render — never rely on the cancelled
            # refresher task having run one more time before we tore it down.
            live.update(build_group(progress, stats, checker.name, checker.color))

    if aborted.is_set():
        console.print(
            f"[yellow]Stopped early: {rate_limit_hits} consecutive rate-limited responses from "
            f"{checker.name}. Remaining usernames were skipped instead of wasting requests.[/yellow]"
        )

    log.info("Checked %d username(s) against %s", len(results), checker.name)
    return results


def build_group(progress: Progress, stats: Stats, platform_name: str, platform_color: str) -> Group:
    return Group(progress, build_stats_table(stats, platform_name, platform_color))


def build_results_table(results: list[CheckResult], color: str) -> Table:
    table = Table(title="Check Results", show_lines=False)
    table.add_column("Platform")
    table.add_column("Username")
    table.add_column("Status", justify="center")
    table.add_column("Response Time", justify="right")
    table.add_column("Method", justify="center")
    table.add_column("Detail", overflow="fold")

    for r in results:
        status_style = STATUS_STYLES[r.status]
        status_label = STATUS_LABELS[r.status]
        method_style = METHOD_STYLES.get(r.method, "white")
        detail = r.detail if r.status != Status.AVAILABLE else ""
        detail_style = "yellow" if r.status == Status.UNKNOWN else "dim"
        table.add_row(
            f"[{color}]{r.platform}[/{color}]",
            r.username,
            f"[{status_style}]{status_label}[/{status_style}]",
            f"{r.response_time * 1000:.0f} ms",
            f"[{method_style}]{r.method}[/{method_style}]",
            f"[{detail_style}]{detail}[/{detail_style}]" if detail else "",
        )
    return table


def save_available(platform_key: str, results: list[CheckResult], config: Config) -> Path | None:
    available = [r.username for r in results if r.status == Status.AVAILABLE]
    if not available or not config.save_available:
        return None

    out_dir = Path(config.output_directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{platform_key}_available_{timestamp}.txt"
    out_path.write_text("\n".join(available) + "\n", encoding="utf-8")
    return out_path


def print_summary(results: list[CheckResult], saved_path: Path | None, config: Config) -> None:
    available = [r for r in results if r.status == Status.AVAILABLE]
    unknown = [r for r in results if r.status == Status.UNKNOWN]

    if saved_path:
        console.print(f"[bold green]Saved {len(available)} available username(s) to {saved_path}[/bold green]")
    elif available:
        console.print(f"[bold green]Found {len(available)} available username(s).[/bold green]")
    else:
        console.print("[yellow]No available usernames found in this batch.[/yellow]")

    if unknown:
        console.print(
            f"\n[yellow]{len(unknown)} of {len(results)} result(s) were UNKNOWN[/yellow] "
            f"(network error, rate limiting, or bot protection). Breakdown:"
        )
        reason_counts: dict[str, int] = {}
        for r in unknown:
            reason = r.detail or "unrecognized response"
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        for reason, count in sorted(reason_counts.items(), key=lambda kv: -kv[1]):
            console.print(f"  [dim]•[/dim] {count}x — {reason}")
        console.print(f"[dim]Full details logged to {config.log_file}.[/dim]")


def run_search(config: Config) -> None:
    """Run one full platform-selection -> generate -> check -> report cycle."""
    log = get_logger()

    platform_key = choose_platform()
    checker_cls = PLATFORM_CHECKERS[platform_key]

    if platform_key == "github" and not config.github_token:
        console.print(
            "[dim]Tip: set GITHUB_TOKEN (env var) or config.yaml to raise your rate limit "
            "from 60 to 5000 requests/hour.[/dim]"
        )
    if platform_key == "twitch" and not (config.twitch_client_id and config.twitch_client_secret):
        console.print(
            "[yellow]Twitch requires TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET "
            "(see config.example.yaml).[/yellow]"
        )
    if checker_cls.method == Method.URL.value:
        console.print(
            f"[dim]{checker_cls.name} has no official availability API — using URL-based "
            f"detection (configurable in config.yaml under platforms.{platform_key}).[/dim]"
        )

    options = choose_generator_options()
    usernames = generate_batch(options)
    console.print(f"[dim]Generated {len(usernames)} unique candidate usernames.[/dim]")

    if platform_key == "github" and not config.github_token and len(usernames) > 60:
        console.print(
            "[yellow]Warning:[/yellow] GitHub allows only 60 anonymous requests/hour. "
            f"You're about to check {len(usernames)} usernames, so this batch will likely hit "
            "the limit partway through and the rest will come back UNKNOWN. Add GITHUB_TOKEN "
            "(env var or config.yaml) to raise this to 5000/hour.\n"
        )

    start = time.monotonic()
    results = asyncio.run(run_checks(platform_key, usernames, config))
    elapsed = time.monotonic() - start

    console.print()
    console.print(build_results_table(results, checker_cls.color))

    saved_path = save_available(platform_key, results, config)
    print_summary(results, saved_path, config)
    console.print(f"\n[dim]Done in {elapsed:.1f}s.[/dim]")
    log.info("Session finished in %.1fs (%d checked)", elapsed, len(results))


def ask_again_or_exit() -> bool:
    """Ask the user whether to search again or exit. Returns True to continue."""
    console.print()
    choice = Prompt.ask(
        "[bold]What would you like to do?[/bold]",
        choices=["again", "exit"],
        default="again",
    )
    return choice == "again"


def main() -> None:
    clear_screen()
    show_banner()

    config = Config.load()
    ensure_directories(config)
    setup_logging(
        log_file=config.log_file,
        level=config.log_level,
        max_bytes=config.log_max_bytes,
        backup_count=config.log_backup_count,
    )
    log = get_logger()
    log.info("GitMeName v%s session started", config.app_version)

    if not Confirm.ask("Ready to start?", default=True):
        console.print("[dim]Goodbye.[/dim]")
        return

    while True:
        run_search(config)

        if not ask_again_or_exit():
            console.print("[dim]Goodbye.[/dim]")
            log.info("Session ended by user (exit)")
            break

        console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted. Goodbye.[/dim]")
