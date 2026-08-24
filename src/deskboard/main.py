"""DeskBoard application entry point."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from deskboard.app.application import DeskBoardApplication, as_qt_application
from deskboard.app.single_instance import InstanceRole, SingleInstanceGuard
from deskboard.infrastructure.logging_setup import configure_logging
from deskboard.infrastructure.paths import RuntimePaths, ensure_runtime_dirs


@dataclass(frozen=True)
class Runtime:
    paths: RuntimePaths


SINGLE_INSTANCE_SERVER_NAME = "DeskBoard.SingleInstance.v1"


def initialize_runtime() -> Runtime:
    """Create the supported runtime directories and configure DeskBoard logs."""
    paths = ensure_runtime_dirs()
    logger = configure_logging(paths.logs)
    logger.info("DeskBoard runtime initialized")
    return Runtime(paths=paths)


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv if argv is None else argv)
    runtime = initialize_runtime()
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from deskboard.database.connection import connect_database
    from deskboard.database.schema import migrate
    from deskboard.infrastructure.clock import SystemClock
    from deskboard.presentation.weather_presenter import WeatherPresenter
    from deskboard.providers.weather.provider import WeatherProvider
    from deskboard.repositories.course_repository import CourseRepository
    from deskboard.repositories.network_repository import NetworkRepository
    from deskboard.repositories.profile_repository import ProfileRepository
    from deskboard.repositories.settings_repository import SettingsRepository
    from deskboard.repositories.todo_repository import TodoRepository
    from deskboard.repositories.weather_repository import WeatherRepository
    from deskboard.services.agenda_service import AgendaService
    from deskboard.services.course_service import CourseService
    from deskboard.services.profile_service import ProfileService
    from deskboard.services.refresh_service import DataRefreshService
    from deskboard.services.settings_service import SettingsService
    from deskboard.services.status_service import StatusService
    from deskboard.services.timetable_service import TimetableService
    from deskboard.services.todo_service import TodoService
    from deskboard.services.weather_service import WeatherService
    from deskboard.ui.dashboard.window import DashboardWindow
    from deskboard.ui.settings.window import SettingsWindow

    qt_application = QApplication.instance() or QApplication(arguments)
    qt_application.setApplicationName("DeskBoard")
    application_holder: list[DeskBoardApplication] = []
    instance_guard = SingleInstanceGuard(
        SINGLE_INSTANCE_SERVER_NAME,
        lambda: application_holder[0].show_settings() if application_holder else None,
    )
    if instance_guard.start() is InstanceRole.SECONDARY:
        return 0
    connection = connect_database(runtime.paths.database)
    migrate(connection)
    clock = SystemClock()
    settings_repository = SettingsRepository(connection)
    settings_service = SettingsService(settings_repository)
    todo_service = TodoService(TodoRepository(connection), clock)
    course_service = CourseService(CourseRepository(connection), clock)
    profile_service = ProfileService(ProfileRepository(connection), clock, settings_repository)
    agenda_service = AgendaService(todo_service, course_service)
    timetable_service = TimetableService(todo_service, course_service)
    network_repository = NetworkRepository(connection)
    weather_service = WeatherService(WeatherRepository(connection))
    weather_provider = WeatherProvider(cities=weather_service.list_cities())
    status_service = StatusService(network_repository, items=weather_provider.items)
    refresh_service = DataRefreshService(
        network_repository,
        clock,
        providers=[weather_provider],
        items=weather_provider.items,
        status_service=status_service,
        settings_service=settings_service,
    )
    weather_presenter = WeatherPresenter(weather_service, refresh_service)
    qt_application.aboutToQuit.connect(connection.close)
    dashboard = DashboardWindow(
        todo_service=todo_service,
        agenda_service=agenda_service,
        timetable_service=timetable_service,
        profile_service=profile_service,
        clock=clock,
        weather_presenter=weather_presenter,
        network_status_service=status_service,
        refresh_service=refresh_service,
    )
    refresh_service.startup()

    def make_settings(set_mode, show_dashboard, hide_dashboard, exit_application):
        return SettingsWindow(
            set_mode,
            show_dashboard,
            hide_dashboard,
            exit_application,
            todo_service=todo_service,
            clock=clock,
            on_todos_changed=dashboard.bridge.publish_todos,
        )

    application = DeskBoardApplication(
        as_qt_application(qt_application),
        dashboard_factory=lambda: dashboard,
        settings_factory=make_settings,
        instance_guard=instance_guard,
    )
    application_holder.append(application)
    application.start(open_settings=False)
    if "--smoke" in arguments:
        QTimer.singleShot(2_000, qt_application.quit)
    return application.run()
