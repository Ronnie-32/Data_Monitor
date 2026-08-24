"""QWebChannel bridge for Dashboard state and semantic commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from PySide6.QtCore import QObject, Signal, Slot

from deskboard.app.modes import AppMode
from deskboard.infrastructure.clock import Clock, SystemClock
from deskboard.models.profile import Profile, ProfileState
from deskboard.models.todo import Todo
from deskboard.presentation.agenda_presenter import present_today_agenda
from deskboard.presentation.dashboard_state import present_dashboard_state
from deskboard.presentation.layout_state import present_profile_state
from deskboard.presentation.timetable_presenter import present_timetable
from deskboard.presentation.todo_presenter import present_todos


class TodoServiceLike(Protocol):
    def add_quick(self, content: str) -> Todo: ...

    def set_completed(self, todo_id: int, completed: bool) -> Todo: ...

    def reorder(self, ordered_ids: list[int]) -> None: ...

    def get_dashboard_items(self) -> list[Todo]: ...


class AgendaServiceLike(Protocol):
    def get_today(self, day):
        ...


class TimetableServiceLike(Protocol):
    def get_current_week(self, day, *, header_mode: str = "weekday_date"):
        ...


class ProfileServiceLike(Protocol):
    @property
    def current_profile(self) -> Profile: ...

    def save_current(self, state: ProfileState) -> None: ...

    def save_as(self, name: str, state: ProfileState) -> Profile: ...



class WeatherPresenterLike(Protocol):
    def present(
        self, *, display_mode: str | None = None, max_cities: int | None = None
    ) -> dict[str, object]: ...


class NetworkStatusServiceLike(Protocol):
    @property
    def color(self) -> str: ...


class RefreshServiceLike(Protocol):
    def add_listener(
        self, listener: Callable[[str], None]
    ) -> Callable[[], None]: ...

class DashboardBridge(QObject):
    shellReady = Signal()
    stateChanged = Signal(dict)
    profileChanged = Signal(dict)
    modeChanged = Signal(str)
    settingsRequested = Signal()
    todosChanged = Signal(list)
    agendaChanged = Signal(dict)
    weatherChanged = Signal(dict)
    networkStatusChanged = Signal(dict)
    timetableChanged = Signal(dict)
    weeklyTimetableRequested = Signal()
    layoutEditRequested = Signal()
    layoutSaveRequested = Signal(dict)
    layoutCancelRequested = Signal()
    todoEditorRequested = Signal(int)
    todoDeleteRequested = Signal(int)

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        todo_service: TodoServiceLike | None = None,
        agenda_service: AgendaServiceLike | None = None,
        timetable_service: TimetableServiceLike | None = None,
        profile_service: ProfileServiceLike | None = None,
        clock: Clock | None = None,
        weather_presenter: WeatherPresenterLike | None = None,
        network_status_service: NetworkStatusServiceLike | None = None,
        refresh_service: RefreshServiceLike | None = None,
    ) -> None:
        super().__init__(parent)
        self._todo_service = todo_service
        self._agenda_service = agenda_service
        self._timetable_service = timetable_service
        self._profile_service = profile_service
        self._clock = clock or SystemClock()
        self._mode = AppMode.INTERACTION
        self._profile_state_override: ProfileState | None = None
        self._weather_presenter = weather_presenter
        self._network_status_service = network_status_service
        self._remove_refresh_listener: Callable[[], None] | None = None
        if refresh_service is not None:
            self._remove_refresh_listener = refresh_service.add_listener(
                self._on_refresh_group_finished
            )

    @Slot()
    def notifyReady(self) -> None:  # noqa: N802
        self.shellReady.emit()
        self.publish_todos()

    @Slot()
    def requestInitialState(self) -> None:  # noqa: N802
        """Publish one coarse snapshot for the web render-state mirror."""
        self.shellReady.emit()
        self.publish_state()

    @Slot()
    def openSettings(self) -> None:  # noqa: N802
        self.settingsRequested.emit()

    def publish_mode(self, mode: AppMode) -> None:
        if not isinstance(mode, AppMode):
            raise TypeError("mode must be an AppMode")
        self._mode = mode
        self.modeChanged.emit(mode.value)

    @Slot()
    def enterLayoutEdit(self) -> None:  # noqa: N802
        if self._mode in (AppMode.LOCKED, AppMode.INTERACTION):
            self.layoutEditRequested.emit()

    @Slot("QVariantMap")
    def saveLayout(self, layout_state: dict[str, object]) -> None:  # noqa: N802
        if self._mode is AppMode.LAYOUT_EDIT:
            if not isinstance(layout_state, dict):
                raise TypeError("layout_state must be a mapping")
            self.layoutSaveRequested.emit(dict(layout_state))

    @Slot()
    def cancelLayoutEdit(self) -> None:  # noqa: N802
        if self._mode is AppMode.LAYOUT_EDIT:
            self.layoutCancelRequested.emit()

    @Slot(str)
    def addQuickTodo(self, content: str) -> None:  # noqa: N802
        if not self._todo_commands_enabled():
            return
        assert self._todo_service is not None
        self._todo_service.add_quick(content)
        self.publish_todos()

    @Slot(int)
    def toggleTodo(self, todo_id: int) -> None:  # noqa: N802
        if not self._todo_commands_enabled():
            return
        assert self._todo_service is not None
        current = next(
            (todo for todo in self._todo_service.get_dashboard_items() if todo.id == todo_id),
            None,
        )
        if current is None:
            raise LookupError(f"Todo {todo_id} is not available on the Dashboard")
        self._todo_service.set_completed(todo_id, not current.is_completed)
        self.publish_todos()

    @Slot("QVariantList")
    def reorderTodos(self, ordered_ids: list[object]) -> None:  # noqa: N802
        if not self._todo_commands_enabled():
            return
        ids = [_todo_id(value) for value in ordered_ids]
        assert self._todo_service is not None
        self._todo_service.reorder(ids)
        self.publish_todos()

    @Slot(int)
    def openTodoEditor(self, todo_id: int) -> None:  # noqa: N802
        if not self._todo_commands_enabled():
            return
        self.todoEditorRequested.emit(_todo_id(todo_id))

    @Slot(int)
    def requestDeleteTodo(self, todo_id: int) -> None:  # noqa: N802
        if not self._todo_commands_enabled():
            return
        self.todoDeleteRequested.emit(_todo_id(todo_id))

    @Slot()
    def requestWeeklyTimetable(self) -> None:  # noqa: N802
        if self._mode is AppMode.INTERACTION:
            self.weeklyTimetableRequested.emit()
            self.publish_timetable()

    def publish_timetable(self, *, header_mode: str = "weekday_date") -> None:
        if self._timetable_service is None:
            return
        week = self._timetable_service.get_current_week(
            self._clock.today(),
            header_mode=header_mode,
        )
        self.timetableChanged.emit(present_timetable(week, header_mode=header_mode))

    def publish_todos(self) -> None:
        if self._todo_service is None:
            self.todosChanged.emit([])
        else:
            payload = present_todos(
                self._todo_service.get_dashboard_items(),
                today=self._clock.today(),
                now=self._clock.now(),
            )
            self.todosChanged.emit(payload)
        if self._agenda_service is not None:
            self.publish_agenda()

    def publish_agenda(self) -> None:
        if self._agenda_service is None:
            self.agendaChanged.emit(
                {"date": self._clock.today().isoformat(), "timedItems": [], "dateOnlyItems": []}
            )
            return
        self.agendaChanged.emit(
            present_today_agenda(self._agenda_service.get_today(self._clock.today()))
        )

    def publish_state(self) -> None:
        state = present_dashboard_state(
            todo_service=self._todo_service,
            agenda_service=self._agenda_service,
            clock=self._clock,
            mode=self._mode,
            profile=self._profile_payload(),
            weather_presenter=self._weather_presenter,
            weather_display_mode=self._weather_display_mode(),
            network_status_service=self._network_status_service,
        )
        self.stateChanged.emit(state)
        self.weatherChanged.emit(dict(state["weather"]))
        self.networkStatusChanged.emit(dict(state["networkStatus"]))

    def publish_weather(self) -> dict[str, object]:
        payload = self._weather_payload()
        self.weatherChanged.emit(payload)
        return payload

    def publish_network_status(self) -> dict[str, object]:
        payload = self._network_status_payload()
        self.networkStatusChanged.emit(payload)
        return payload

    def _on_refresh_group_finished(self, group: str) -> None:
        del group
        self.publish_state()

    def _weather_payload(self) -> dict[str, object]:
        if self._weather_presenter is None:
            return {}
        return dict(
            self._weather_presenter.present(
                display_mode=self._weather_display_mode(),
            )
        )

    def _network_status_payload(self) -> dict[str, object]:
        if self._network_status_service is None:
            return {"state": "grey"}
        color = self._network_status_service.color
        return {"state": color if color in {"grey", "green", "red"} else "grey"}

    def _weather_display_mode(self) -> str | None:
        profile = self._profile_service.current_profile if self._profile_service else None
        state = self._profile_state_override or (profile.state if profile else ProfileState())
        for widget in state.widgets:
            if widget.widget_key != "weather":
                continue
            value = widget.config.get("displayMode", widget.config.get("display_mode"))
            return value if isinstance(value, str) else None
        return None

    def publish_profile_state(self, state: ProfileState) -> None:
        if not isinstance(state, ProfileState):
            raise TypeError("state must be a ProfileState")
        self._profile_state_override = state
        self.profileChanged.emit(self._profile_payload())

    def set_profile_state(self, state: ProfileState) -> None:
        """Set the in-memory render state before the Web page requests its snapshot."""

        if not isinstance(state, ProfileState):
            raise TypeError("state must be a ProfileState")
        self._profile_state_override = state

    def publish_profile(self, state: ProfileState | None = None) -> None:
        """Emit the current presentation Profile, optionally using a runtime state."""

        if state is not None:
            self.publish_profile_state(state)
        else:
            self.profileChanged.emit(self._profile_payload())

    def _profile_payload(self) -> dict[str, object]:
        profile = self._profile_service.current_profile if self._profile_service else None
        state = self._profile_state_override or (profile.state if profile else ProfileState())
        return present_profile_state(
            state,
            profile_id=profile.id if profile else None,
            name=profile.name if profile else None,
            is_builtin=profile.is_builtin if profile else None,
        )

    def _todo_commands_enabled(self) -> bool:
        return self._mode is AppMode.INTERACTION and self._todo_service is not None


def _todo_id(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Todo IDs must be integers")
    if value <= 0:
        raise ValueError("Todo IDs must be positive")
    return value
