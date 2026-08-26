"""Build the coarse, JSON-friendly state owned by the Dashboard bridge."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, TypedDict

from deskboard.app.modes import AppMode
from deskboard.infrastructure.clock import Clock
from deskboard.presentation.agenda_presenter import present_today_agenda
from deskboard.presentation.todo_presenter import present_todos


class TodoStateService(Protocol):
    def get_dashboard_items(self): ...


class AgendaStateService(Protocol):
    def get_today(self, day):
        ...




class WeatherPresenterLike(Protocol):
    def present(
        self, *, display_mode: str | None = None, max_cities: int | None = None
    ) -> Mapping[str, object]: ...


class FinancePresenterLike(Protocol):
    def present(
        self, *, category: str | None = None, max_items: int | None = None
    ) -> Mapping[str, object]: ...


class NetworkStatusLike(Protocol):
    @property
    def color(self) -> str: ...
class DashboardState(TypedDict):
    app: dict[str, object]
    profile: dict[str, object]
    widgets: dict[str, object]
    todos: list[dict[str, object]]
    agenda: dict[str, object]
    weather: dict[str, object]
    finance: dict[str, object]
    networkStatus: dict[str, object]


def present_dashboard_state(
    *,
    todo_service: TodoStateService | None,
    agenda_service: AgendaStateService | None,
    clock: Clock,
    mode: AppMode | str = AppMode.INTERACTION,
    profile: Mapping[str, object] | None = None,
    widgets: Mapping[str, object] | None = None,
    weather: Mapping[str, object] | None = None,
    finance: Mapping[str, object] | None = None,
    network_status: Mapping[str, object] | None = None,
    weather_presenter: WeatherPresenterLike | None = None,
    weather_display_mode: str | None = None,
    weather_max_cities: int | None = None,
    finance_presenter: FinancePresenterLike | None = None,
    network_status_service: NetworkStatusLike | None = None,
    language: str = "zh_CN",
) -> DashboardState:
    """Collect current service presentations in one coarse state snapshot.

    The optional sections are intentionally empty until their owning tasks add
    the corresponding services. They remain part of the contract so the web
    page can keep one stable render-state shape as the Dashboard grows.
    """

    today = clock.today()
    agenda = (
        present_today_agenda(agenda_service.get_today(today))
        if agenda_service is not None
        else _empty_agenda(today.isoformat())
    )
    todos = (
        present_todos(
            todo_service.get_dashboard_items(),
            today=today,
            now=clock.now(),
        )
        if todo_service is not None
        else []
    )
    mode_value = mode.value if isinstance(mode, AppMode) else _mode_value(mode)
    weather_state = dict(weather or {})
    if weather_presenter is not None:
        weather_state = dict(
            weather_presenter.present(
                display_mode=weather_display_mode,
                max_cities=weather_max_cities,
            )
        )
    finance_state = dict(finance or {})
    if finance_presenter is not None:
        finance_state = dict(finance_presenter.present())
    network_state = dict(network_status or {"state": "grey"})
    if network_status_service is not None:
        color = network_status_service.color
        network_state = {"state": color if color in {"grey", "green", "red"} else "grey"}
    language_value = language if language in {"zh_CN", "en_US"} else "zh_CN"
    return {
        "app": {
            "mode": mode_value,
            "today": today.isoformat(),
            "language": language_value,
        },
        "profile": dict(profile or {}),
        "widgets": dict(widgets or {"weather": {}, "todo": {}, "today_agenda": {}}),
        "todos": todos,
        "agenda": agenda,
        "weather": weather_state,
        "finance": finance_state,
        "networkStatus": network_state,
    }


def build_dashboard_state(**kwargs) -> DashboardState:
    """Compatibility alias for callers that name the operation as a builder."""

    return present_dashboard_state(**kwargs)


class DashboardStatePresenter:
    """Reusable presenter bound to the Dashboard's service dependencies."""

    def __init__(
        self,
        *,
        todo_service: TodoStateService | None,
        agenda_service: AgendaStateService | None,
        clock: Clock,
        finance_presenter: FinancePresenterLike | None = None,
    ) -> None:
        self._todo_service = todo_service
        self._agenda_service = agenda_service
        self._clock = clock
        self._finance_presenter = finance_presenter

    def present(self, *, mode: AppMode | str = AppMode.INTERACTION) -> DashboardState:
        return present_dashboard_state(
            todo_service=self._todo_service,
            agenda_service=self._agenda_service,
            clock=self._clock,
            mode=mode,
            finance_presenter=self._finance_presenter,
        )


def _empty_agenda(day: str) -> dict[str, object]:
    return {"date": day, "timedItems": [], "dateOnlyItems": []}


def _mode_value(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError("mode must be an AppMode or non-empty string")
    return value
