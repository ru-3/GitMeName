"""
utils/stats.py
---------------
Live statistics tracked while checks are running: totals, available,
taken, unknown, elapsed time, and requests/sec.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class Stats:
    total_checked: int = 0
    available: int = 0
    taken: int = 0
    unknown: int = 0
    _start_time: float = field(default_factory=time.monotonic)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def record(self, status: str) -> None:
        async with self._lock:
            self.total_checked += 1
            if status == "available":
                self.available += 1
            elif status == "taken":
                self.taken += 1
            elif status == "unknown":
                self.unknown += 1

    @property
    def elapsed_seconds(self) -> float:
        return time.monotonic() - self._start_time

    @property
    def requests_per_second(self) -> float:
        elapsed = self.elapsed_seconds
        return self.total_checked / elapsed if elapsed > 0 else 0.0
