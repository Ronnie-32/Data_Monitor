"""Todo domain values independent of persistence and UI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Final


class _Unset:
    __slots__ = ()


UNSET: Final = _Unset()


@dataclass(frozen=True, slots=True)
class Todo:
    id: int
    content: str
    deadline_date: date | None
    deadline_time: time | None
    planned_date: date | None
    planned_start_time: time | None
    planned_end_time: time | None
    completed_at: datetime | None
    display_order: int
    created_at: datetime
    updated_at: datetime

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None


@dataclass(frozen=True, slots=True)
class TodoUpdate:
    """Partial Todo edit; ``None`` clears a field and ``UNSET`` preserves it."""

    content: str | None | _Unset = UNSET
    deadline_date: date | None | _Unset = UNSET
    deadline_time: time | None | _Unset = UNSET
    planned_date: date | None | _Unset = UNSET
    planned_start_time: time | None | _Unset = UNSET
    planned_end_time: time | None | _Unset = UNSET
