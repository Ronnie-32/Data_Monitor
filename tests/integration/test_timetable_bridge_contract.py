from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path

from deskboard.app.modes import AppMode
from deskboard.models.course import ClassPeriod
from deskboard.presentation.timetable_presenter import present_timetable
from deskboard.services.timetable_service import TimetableEvent, TimetableWeek
from deskboard.ui.dashboard.bridge import DashboardBridge


class FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 21, 12)

    def today(self) -> date:
        return date(2026, 8, 21)


class FakeTimetableService:
    def __init__(self) -> None:
        self.calls: list[tuple[date, str]] = []

    def get_current_week(
        self, day: date, *, header_mode: str = "weekday_date"
    ) -> TimetableWeek:
        self.calls.append((day, header_mode))
        week_dates = [date(2026, 8, 17 + offset) for offset in range(7)]
        return TimetableWeek(
            week_start=week_dates[0],
            week_end=week_dates[-1],
            week_dates=week_dates,
            week_label="第 1 周",
            events=[
                TimetableEvent(
                    id=7,
                    type="todo",
                    title="复习",
                    date=date(2026, 8, 21),
                    start=time(10),
                    end=None,
                    time_kind="point",
                )
            ],
            periods=[
                ClassPeriod(period_no=index, start_time=time(7 + index), end_time=time(8 + index))
                for index in range(1, 9)
            ],
            visible_start=time(8),
            visible_end=time(16),
            headers=[f"header-{offset}" for offset in range(7)],
        )


def test_weekly_timetable_request_is_python_presented_and_mode_gated():
    service = FakeTimetableService()
    bridge = DashboardBridge(
        timetable_service=service,
        clock=FakeClock(),
    )
    requests: list[bool] = []
    payloads: list[dict[str, object]] = []
    bridge.weeklyTimetableRequested.connect(lambda: requests.append(True))
    bridge.timetableChanged.connect(payloads.append)

    bridge.publish_mode(AppMode.LOCKED)
    bridge.requestWeeklyTimetable()
    assert requests == []
    assert payloads == []
    assert service.calls == []

    bridge.publish_mode(AppMode.INTERACTION)
    bridge.requestWeeklyTimetable()

    assert requests == [True]
    assert service.calls == [(date(2026, 8, 21), "weekday_date")]
    assert payloads == [present_timetable(service.get_current_week(date(2026, 8, 21)))]
    assert payloads[0]["weekStart"] == "2026-08-17"
    assert payloads[0]["events"][0]["timeKind"] == "point"


def test_dashboard_web_assets_define_single_page_view_only_timetable_overlay():
    web_root = Path("src/deskboard/ui/dashboard/web")
    html = (web_root / "index.html").read_text(encoding="utf-8")
    app = (web_root / "js/app.js").read_text(encoding="utf-8")
    bridge = (web_root / "js/bridge.js").read_text(encoding="utf-8")
    agenda = (web_root / "js/widgets/agenda.js").read_text(encoding="utf-8")
    timetable = (web_root / "js/timetable.js").read_text(encoding="utf-8")
    css = (web_root / "css/timetable.css").read_text(encoding="utf-8")
    window_source = Path("src/deskboard/ui/dashboard/window.py").read_text(encoding="utf-8")
    main_source = Path("src/deskboard/main.py").read_text(encoding="utf-8")

    assert './css/timetable.css' in html
    assert 'id="timetable-overlay"' in html
    assert "createTimetableOverlay" in app
    assert "timetableChanged" in bridge
    assert "requestWeeklyTimetable" in agenda
    assert "configurationRequired" in timetable
    assert "visibleStart" in timetable and "visibleEnd" in timetable
    assert "headers" in timetable and "periods" in timetable
    assert "position: absolute" in css
    assert "QWebEngineView" not in timetable
    assert "get_occurrences" not in timetable
    assert "timetable_service=timetable_service" in window_source
    assert "TimetableService(todo_service, course_service)" in main_source
