from deskboard.app.application import DeskBoardApplication
from deskboard.app.modes import AppMode


class FakeQtApplication:
    def __init__(self) -> None:
        self.quit_on_last_window_closed = True
        self.exec_calls = 0

    def setQuitOnLastWindowClosed(self, enabled: bool) -> None:  # noqa: N802
        self.quit_on_last_window_closed = enabled

    def exec(self) -> int:
        self.exec_calls += 1
        return 7


class FakeDashboard:
    def __init__(self) -> None:
        self.visible = False
        self.modes: list[AppMode] = []

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False

    def set_mode(self, mode: AppMode) -> None:
        self.modes.append(mode)


class FakeSettings:
    def __init__(self, set_mode, show_dashboard, hide_dashboard) -> None:
        self.set_mode = set_mode
        self.show_dashboard = show_dashboard
        self.hide_dashboard = hide_dashboard
        self.visible = False
        self.close_calls = 0
        self.raise_calls = 0
        self.activate_calls = 0
        self.modes: list[AppMode] = []

    def show(self) -> None:
        self.visible = True

    def close(self) -> None:
        self.visible = False
        self.close_calls += 1

    def raise_(self) -> None:
        self.raise_calls += 1

    def activateWindow(self) -> None:  # noqa: N802
        self.activate_calls += 1

    def set_mode_state(self, mode: AppMode) -> None:
        self.modes.append(mode)


def make_application():
    qt_app = FakeQtApplication()
    dashboard = FakeDashboard()
    settings_instances: list[FakeSettings] = []

    def settings_factory(set_mode, show_dashboard, hide_dashboard):
        settings = FakeSettings(set_mode, show_dashboard, hide_dashboard)
        settings_instances.append(settings)
        return settings

    application = DeskBoardApplication(
        qt_app,
        dashboard_factory=lambda: dashboard,
        settings_factory=settings_factory,
    )
    return application, qt_app, dashboard, settings_instances


def test_start_shows_one_dashboard_in_interaction_mode_and_opens_settings():
    application, qt_app, dashboard, settings_instances = make_application()

    application.start(open_settings=True)

    assert qt_app.quit_on_last_window_closed is False
    assert dashboard.visible is True
    assert dashboard.modes == [AppMode.INTERACTION]
    assert len(settings_instances) == 1
    assert settings_instances[0].visible is True


def test_mode_changes_are_applied_to_dashboard_and_settings_shell():
    application, _, dashboard, settings_instances = make_application()
    application.start(open_settings=True)

    application.set_mode(AppMode.LOCKED)
    application.set_mode(AppMode.LAYOUT_EDIT)

    assert application.mode is AppMode.LAYOUT_EDIT
    assert dashboard.modes[-2:] == [AppMode.LOCKED, AppMode.LAYOUT_EDIT]
    assert settings_instances[0].modes[-2:] == [AppMode.LOCKED, AppMode.LAYOUT_EDIT]


def test_closing_settings_does_not_quit_or_close_dashboard():
    application, qt_app, dashboard, settings_instances = make_application()
    application.start(open_settings=True)

    application.close_settings()

    assert settings_instances[0].close_calls == 1
    assert dashboard.visible is True
    assert qt_app.exec_calls == 0


def test_run_owns_the_event_loop_without_creating_more_windows():
    application, qt_app, _, settings_instances = make_application()
    application.start(open_settings=False)

    assert application.run() == 7
    assert qt_app.exec_calls == 1
    assert settings_instances == []
