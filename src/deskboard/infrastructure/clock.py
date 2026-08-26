"""Windows-system-local clock abstraction for deterministic domain logic."""

from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta
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


def next_local_midnight(value: datetime) -> datetime:
    """Return the next midnight in the same naive Windows-local time basis."""

    if not isinstance(value, datetime):
        raise TypeError("clock value must be a datetime")
    if value.tzinfo is not None:
        raise ValueError("DeskBoard clock values must be timezone-naive")
    return datetime.combine(value.date() + timedelta(days=1), time.min)


def milliseconds_until_next_local_midnight(value: datetime) -> int:
    """Return a positive Qt timer interval until the next local midnight."""

    remaining = (next_local_midnight(value) - value).total_seconds()
    return max(1, math.ceil(remaining * 1000))
