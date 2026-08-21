"""Windows-system-local clock abstraction for deterministic domain logic."""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...

    def today(self) -> date: ...


class SystemClock:
    """Read the process host's local wall clock without a separate timezone."""

    def now(self) -> datetime:
        return datetime.now()

    def today(self) -> date:
        return self.now().date()
