from deskboard.app.application import DeskBoardApplication
from deskboard.app.modes import AppMode


class FakeQtApplication:
    def __init__(self) -> None:
        self.quit_on_last_window_closed = True
        self.exec_calls = 0
        self.quit_calls = 0

    def setQuitOnLastWindowClosed(self, enabled: bool) -> None:  # noqa: N802
        self.quit_on_last_window_closed = enabled

    def exec(self) -> int:
        self.exec_calls += 1
        return 7

    def quit(self) -> None:
        self.quit_calls += 1


class FakeDashboard:
    def __init__(self) -> None:
        self.visible = False
        self.modes: list[AppMode] = []

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False

    def isVisible(self) -> bool:  # noqa: N802
        return self.visible

    def set_mode(self, mode: AppMode) -> None:
        self.modes.append(mode)


class FakeSettings:
    def __init__(self, set_mode, show_dashboard, hide_dashboard, exit_application) -> None:
        self.set_mode = set_mode
        self.show_dashboard = show_dashboard
        self.hide_dashboard = hide_dashboard
        self.exit_application = exit_application
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


class FakeTray:
    def __init__(
        self,
        toggle_dashboard,
        set_locked,
        set_interaction,
        show_settings,
        exit_application,
    ) -> None:
        self.toggle_dashboard = toggle_dashboard
        self.set_locked = set_locked
        self.set_interaction = set_interaction
        self.show_settings = show_settings
        self.exit_application = exit_application
        self.show_calls = 0
        self.hide_calls = 0
        self.dashboard_visibility = []

    def show(self) -> None:
        self.show_calls += 1

    def hide(self) -> None:
        self.hide_calls += 1

    def sync_dashboard_visibility(self, visible: bool) -> None:
        self.dashboard_visibility.append(visible)


class FakeInstanceGuard:
    def __init__(self) -> None:
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


def make_application():
    qt_app = FakeQtApplication()
    dashboard = FakeDashboard()
    settings_instances: list[FakeSettings] = []
    tray_instances: list[FakeTray] = []
    instance_guard = FakeInstanceGuard()

    def settings_factory(set_mode, show_dashboard, hide_dashboard, exit_application):
        settings = FakeSettings(
            set_mode,
            show_dashboard,
            hide_dashboard,
            exit_application,
        )
        settings_instances.append(settings)
        return settings

    def tray_factory(*callbacks):
        tray = FakeTray(*callbacks)
        tray_instances.append(tray)
        return tray

    application = DeskBoardApplication(
        qt_app,
        dashboard_factory=lambda: dashboard,
        settings_factory=settings_factory,
        tray_factory=tray_factory,
        instance_guard=instance_guard,
    )
    return application, qt_app, dashboard, settings_instances, tray_instances


def test_start_shows_one_dashboard_in_interaction_mode_and_opens_settings():
    application, qt_app, dashboard, settings_instances, tray_instances = make_application()

    application.start(open_settings=True)

    assert qt_app.quit_on_last_window_closed is False
    assert dashboard.visible is True
    assert dashboard.modes == [AppMode.INTERACTION]
    assert len(settings_instances) == 1
    assert settings_instances[0].visible is True
    assert tray_instances[0].show_calls == 1


def test_mode_changes_are_applied_to_dashboard_and_settings_shell():
    application, _, dashboard, settings_instances, _ = make_application()
    application.start(open_settings=True)

    application.set_mode(AppMode.LOCKED)
    application.set_mode(AppMode.LAYOUT_EDIT)

    assert application.mode is AppMode.LAYOUT_EDIT
    assert dashboard.modes[-2:] == [AppMode.LOCKED, AppMode.LAYOUT_EDIT]
    assert settings_instances[0].modes[-2:] == [AppMode.LOCKED, AppMode.LAYOUT_EDIT]


def test_closing_settings_does_not_quit_or_close_dashboard():
    application, qt_app, dashboard, settings_instances, _ = make_application()
    application.start(open_settings=True)

    application.close_settings()

    assert settings_instances[0].close_calls == 1
    assert dashboard.visible is True
    assert qt_app.exec_calls == 0


def test_run_owns_the_event_loop_without_creating_more_windows():
    application, qt_app, _, settings_instances, _ = make_application()
    application.start(open_settings=False)

    assert application.run() == 7
    assert qt_app.exec_calls == 1
    assert settings_instances == []


def test_tray_callbacks_toggle_dashboard_and_switch_only_daily_modes():
    application, _, dashboard, _, tray_instances = make_application()
    application.start()
    tray = tray_instances[0]

    tray.toggle_dashboard()
    assert dashboard.visible is False
    assert tray.dashboard_visibility[-1] is False

    tray.toggle_dashboard()
    tray.set_locked()
    tray.set_interaction()

    assert dashboard.visible is True
    assert tray.dashboard_visibility[-1] is True
    assert dashboard.modes[-2:] == [AppMode.LOCKED, AppMode.INTERACTION]


def test_settings_exit_quits_the_owned_application_shell():
    application, qt_app, dashboard, settings_instances, tray_instances = make_application()
    application.start(open_settings=True)

    settings_instances[0].exit_application()

    assert qt_app.quit_calls == 1
    assert dashboard.visible is False
    assert settings_instances[0].close_calls == 1
    assert tray_instances[0].hide_calls == 1


def test_tray_exit_quits_the_owned_application_shell():
    application, qt_app, dashboard, _, tray_instances = make_application()
    application.start()

    tray_instances[0].exit_application()

    assert qt_app.quit_calls == 1
    assert dashboard.visible is False
    assert tray_instances[0].hide_calls == 1


def test_exit_closes_guard_then_owned_windows_and_quits_exactly_once():
    application, qt_app, dashboard, settings_instances, tray_instances = make_application()
    application.start(open_settings=True)
    events = []
    guard = application.instance_guard
    guard.close = lambda: events.append("guard")
    settings_instances[0].close = lambda: events.append("settings")
    dashboard.hide = lambda: events.append("dashboard")
    tray_instances[0].hide = lambda: events.append("tray")
    qt_app.quit = lambda: events.append("quit")

    application.exit()
    application.exit()

    assert events == ["guard", "settings", "dashboard", "tray", "quit"]
