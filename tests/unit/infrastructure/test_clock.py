from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from deskboard.infrastructure.clock import Clock, SystemClock


@dataclass
class FakeClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def today(self) -> date:
        return self.current.date()


def test_system_clock_uses_current_local_time_and_one_source_for_today():
    clock = SystemClock()
    before = datetime.now()

    observed = clock.now()

    after = datetime.now()
    assert observed.tzinfo is None
    assert before <= observed <= after
    assert clock.today() == clock.now().date()


def test_fake_clock_pattern_is_deterministic_and_matches_protocol():
    clock: Clock = FakeClock(datetime(2026, 8, 21, 23, 59, 58))

    assert clock.now() == datetime(2026, 8, 21, 23, 59, 58)
    assert clock.today() == date(2026, 8, 21)
    clock.current = datetime(2026, 8, 22, 0, 0, 1)
    assert clock.today() == date(2026, 8, 22)
