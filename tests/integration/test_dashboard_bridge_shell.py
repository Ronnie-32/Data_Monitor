from pathlib import Path

from deskboard.app.modes import AppMode
from deskboard.ui.dashboard.bridge import DashboardBridge
from deskboard.ui.dashboard.window import DashboardWindow
from deskboard.ui.settings.window import SettingsWindow


def test_bridge_reports_web_readiness_and_publishes_mode():
    bridge = DashboardBridge()
    ready_events: list[bool] = []
    mode_events: list[str] = []
    bridge.shellReady.connect(lambda: ready_events.append(True))
    bridge.modeChanged.connect(mode_events.append)

    bridge.notifyReady()
    bridge.publish_mode(AppMode.LOCKED)

    assert ready_events == [True]
    assert mode_events == ["locked"]


def test_dashboard_declares_exactly_one_webengine_view_and_local_page():
    source = Path(DashboardWindow.__module__.replace(".", "/") + ".py")
    source = Path("src") / source
    text = source.read_text(encoding="utf-8")
    html = DashboardWindow.web_page_path().read_text(encoding="utf-8")

    assert text.count("QWebEngineView(") == 1
    assert "setMinimumSize(" not in text
    assert "qrc:///qtwebchannel/qwebchannel.js" in html
    assert "bridge.notifyReady()" in html
    assert "http://" not in html
    assert "https://" not in html


def test_native_settings_shell_has_exactly_the_eight_approved_pages():
    assert SettingsWindow.PAGE_TITLES == (
        "General",
        "Profiles",
        "Weather",
        "Finance",
        "Todo",
        "Courses",
        "Data Status",
        "About",
    )
