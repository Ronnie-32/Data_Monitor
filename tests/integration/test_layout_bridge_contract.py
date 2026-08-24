from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from deskboard.app.modes import AppMode
from deskboard.infrastructure.clock import Clock
from deskboard.models.profile import Profile, ProfileState, ProfileWidgetState
from deskboard.ui.dashboard import window as window_module
from deskboard.ui.dashboard.bridge import DashboardBridge
from deskboard.ui.dashboard.window import DashboardWindow


class FakeClock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 8, 21, 9, 30)

    def today(self):
        return self.now().date()


class FakeProfileService:
    def __init__(self, *, builtin: bool) -> None:
        state = ProfileState(
            widgets=(
                ProfileWidgetState("todo", True, 0, 0, 6, 6),
                ProfileWidgetState("today_agenda", True, 6, 0, 6, 6),
            )
        )
        self.current_profile = Profile(
            id=1,
            name="Default" if builtin else "Study",
            is_builtin=builtin,
            state=state,
            created_at=datetime(2026, 8, 21, 9),
            updated_at=datetime(2026, 8, 21, 9),
        )
        self.saved: list[ProfileState] = []

    def save_current(self, state: ProfileState) -> None:
        self.saved.append(state)

    def save_as(self, name: str, state: ProfileState) -> Profile:
        self.saved.append(state)
        self.current_profile = Profile(
            id=2,
            name=name,
            is_builtin=False,
            state=state,
            created_at=self.current_profile.created_at,
            updated_at=self.current_profile.updated_at,
        )
        return self.current_profile


def test_layout_commands_are_mode_gated_and_emit_one_save_cancel_request():
    bridge = DashboardBridge()
    entered: list[bool] = []
    saved: list[dict[str, object]] = []
    cancelled: list[bool] = []
    bridge.layoutEditRequested.connect(lambda: entered.append(True))
    bridge.layoutSaveRequested.connect(saved.append)
    bridge.layoutCancelRequested.connect(lambda: cancelled.append(True))

    bridge.publish_mode(AppMode.LOCKED)
    bridge.enterLayoutEdit()
    bridge.saveLayout({"columnCount": 12, "widgets": []})
    bridge.cancelLayoutEdit()

    bridge.publish_mode(AppMode.INTERACTION)
    bridge.enterLayoutEdit()
    bridge.publish_mode(AppMode.LAYOUT_EDIT)
    payload = {"columnCount": 12, "widgets": [{"widgetKey": "todo", "x": 1}]}
    bridge.saveLayout(payload)
    bridge.cancelLayoutEdit()

    assert entered == [True, True]
    assert saved == [payload]
    assert cancelled == [True]


def test_profile_changed_event_is_dashboard_owned_and_serializable():
    bridge = DashboardBridge()
    events: list[dict[str, object]] = []
    bridge.profileChanged.connect(events.append)

    bridge.publish_profile_state(
        ProfileState(
            widgets=(ProfileWidgetState("todo", True, 0, 0, 6, 5),),
        )
    )

    assert events[0]["columnCount"] == 12
    assert events[0]["widgets"][0]["widgetKey"] == "todo"


def test_web_layout_contract_uses_local_gridstack_and_defers_persistence_until_save():
    web_root = Path("src/deskboard/ui/dashboard/web")
    html = (web_root / "index.html").read_text(encoding="utf-8")
    app = (web_root / "js/app.js").read_text(encoding="utf-8")
    layout = (web_root / "js/layout.js").read_text(encoding="utf-8")

    assert "./vendor/gridstack/gridstack-all.js" in html
    assert "./vendor/gridstack/gridstack.min.css" in html
    assert "id=\"layout-toolbar\"" in html
    assert "saveLayout" in layout
    assert "cancelLayoutEdit" in layout
    assert "column: 12" in layout
    assert "createLayoutController" in app
    assert "grid.on(\"change\"" in layout
    assert "profileChanged" in app


def test_grid_layout_clamps_items_to_board_edges_with_small_horizontal_gap():
    web_root = Path("src/deskboard/ui/dashboard/web")
    layout = (web_root / "js/layout.js").read_text(encoding="utf-8")
    css = (web_root / "css/layout.css").read_text(encoding="utf-8")

    assert "LAYOUT_EDGE_PADDING_PX = 0" in layout
    assert "computeMaxRows" in layout
    assert "clampGridItemToBoard" in layout
    assert "grid.engine.maxRow" in layout
    assert "--gs-item-margin-top: 0px" in css
    assert "--gs-item-margin-bottom: 0px" in css
    assert "--gs-item-margin-left: 4px" in css
    assert "--gs-item-margin-right: 4px" in css


def test_default_layout_uses_a_small_horizontal_region_gap():
    web_root = Path("src/deskboard/ui/dashboard/web")
    html = (web_root / "index.html").read_text(encoding="utf-8")
    layout = (web_root / "js/layout.js").read_text(encoding="utf-8")
    css = (web_root / "css/layout.css").read_text(encoding="utf-8")

    assert "LAYOUT_HORIZONTAL_GAP_PX = 4" in layout
    assert "--gs-item-margin-left: 4px" in css
    assert "--gs-item-margin-right: 4px" in css
    assert 'gs-x="1" gs-y="0" gs-w="5"' in html
    assert 'gs-x="6" gs-y="0" gs-w="5"' in html


def test_grid_layout_cell_height_fills_board_without_fractional_row_remainder():
    layout = Path("src/deskboard/ui/dashboard/web/js/layout.js").read_text(encoding="utf-8")

    assert "computeGridMetrics" in layout
    assert "cellHeight: height / maxRows" in layout
    assert "updateGridBounds(metrics.maxRows)" in layout


def test_outer_board_resize_preserves_required_rows_while_recomputing_pixels():
    layout = Path("src/deskboard/ui/dashboard/web/js/layout.js").read_text(encoding="utf-8")

    assert "requiredRows = 1" in layout
    assert "Math.max(naturalRows, requiredRows)" in layout
    assert "boardRowCount" in layout


def test_real_qwebchannel_invokes_layout_save_slot():
    app = QApplication.instance() or QApplication([])
    view = QWebEngineView()
    bridge = DashboardBridge()
    bridge.publish_mode(AppMode.LAYOUT_EDIT)
    saved: list[dict[str, object]] = []
    bridge.layoutSaveRequested.connect(saved.append)
    channel = QWebChannel(view.page())
    channel.registerObject("bridge", bridge)
    view.page().setWebChannel(channel)

    html = """
    <!doctype html><html><body>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
      new QWebChannel(qt.webChannelTransport, function (channel) {
        channel.objects.bridge.saveLayout({
          columnCount: 12,
          widgets: [{widgetKey: "todo", x: 1, y: 2, w: 6, h: 5}]
        });
      });
    </script></body></html>
    """
    loop = QEventLoop()
    bridge.layoutSaveRequested.connect(loop.quit)
    view.setHtml(html)
    QTimer.singleShot(5000, loop.quit)
    loop.exec()

    assert saved == [
        {"columnCount": 12, "widgets": [{"widgetKey": "todo", "x": 1, "y": 2, "w": 6, "h": 5}]}
    ]
    view.deleteLater()
    del app


def test_dashboard_window_save_and_cancel_restore_the_recorded_daily_mode():
    app = QApplication.instance() or QApplication([])
    profile_service = FakeProfileService(builtin=False)
    window = DashboardWindow(profile_service=profile_service, clock=FakeClock())
    window.setGeometry(10, 20, 600, 400)
    window.set_mode(AppMode.LOCKED)
    window.set_mode(AppMode.LAYOUT_EDIT)
    window.setGeometry(40, 50, 800, 500)
    window.bridge.cancelLayoutEdit()

    assert window.mode is AppMode.LOCKED
    geometry = (
        window.geometry().x(),
        window.geometry().y(),
        window.geometry().width(),
        window.geometry().height(),
    )
    assert geometry == (
        10,
        20,
        600,
        400,
    )
    assert profile_service.saved == []

    window.set_mode(AppMode.LAYOUT_EDIT)
    window.bridge.saveLayout(
        {
            "columnCount": 12,
            "widgets": [
                {"widgetKey": "todo", "visible": True, "x": 1, "y": 1, "w": 5, "h": 5},
                {
                    "widgetKey": "today_agenda",
                    "visible": True,
                    "x": 6,
                    "y": 1,
                    "w": 6,
                    "h": 5,
                },
            ],
        }
    )

    assert window.mode is AppMode.LOCKED
    assert profile_service.saved[0].widgets[0].x == 1
    window.close()
    del app


def test_default_save_uses_native_save_as_and_dismiss_keeps_edit_open(monkeypatch):
    app = QApplication.instance() or QApplication([])
    profile_service = FakeProfileService(builtin=True)
    window = DashboardWindow(profile_service=profile_service, clock=FakeClock())
    window.set_mode(AppMode.LAYOUT_EDIT)

    monkeypatch.setattr(
        window_module.QInputDialog,
        "getText",
        staticmethod(lambda *_args, **_kwargs: ("Study", True)),
    )
    window.bridge.saveLayout(
        {
            "columnCount": 12,
            "widgets": [{"widgetKey": "todo", "visible": True, "x": 0, "y": 0, "w": 6, "h": 6}],
        }
    )

    assert window.mode is AppMode.INTERACTION
    assert profile_service.current_profile.name == "Study"
    assert len(profile_service.saved) == 1
    window.close()

    dismissed_service = FakeProfileService(builtin=True)
    dismissed_window = DashboardWindow(
        profile_service=dismissed_service,
        clock=FakeClock(),
    )
    dismissed_window.set_mode(AppMode.LAYOUT_EDIT)
    monkeypatch.setattr(
        window_module.QInputDialog,
        "getText",
        staticmethod(lambda *_args, **_kwargs: ("", False)),
    )
    dismissed_window.bridge.saveLayout(
        {"columnCount": 12, "widgets": [{"widgetKey": "todo", "x": 0, "y": 0, "w": 6, "h": 6}]}
    )

    assert dismissed_window.mode is AppMode.LAYOUT_EDIT
    assert dismissed_service.current_profile.name == "Default"
    assert dismissed_service.saved == []
    dismissed_window.close()
    del app


def test_dashboard_web_page_loads_local_gridstack_layout_shell():
    app = QApplication.instance() or QApplication([])
    window = DashboardWindow(clock=FakeClock())
    loaded: list[bool] = []
    window.view.loadFinished.connect(loaded.append)
    window.show()
    load_loop = QEventLoop()
    window.view.loadFinished.connect(load_loop.quit)
    QTimer.singleShot(5000, load_loop.quit)
    load_loop.exec()

    assert loaded and loaded[-1] is True
    values: list[object] = []
    evaluate_loop = QEventLoop()
    window.view.page().runJavaScript(
        "JSON.stringify({grid: typeof GridStack, items: "
        "document.querySelectorAll('.grid-stack-item').length, "
        "toolbar: document.getElementById('layout-toolbar').hidden})",
        lambda value: (values.append(value), evaluate_loop.quit()),
    )
    QTimer.singleShot(5000, evaluate_loop.quit)
    evaluate_loop.exec()

    assert values == ['{"grid":"function","items":2,"toolbar":true}']
    window.close()
    del app


def test_outer_dashboard_resize_recomputes_grid_pixels_without_reflowing_coordinates():
    app = QApplication.instance() or QApplication([])
    window = DashboardWindow(clock=FakeClock())
    window.show()
    load_loop = QEventLoop()
    window.view.loadFinished.connect(load_loop.quit)
    QTimer.singleShot(5000, load_loop.quit)
    load_loop.exec()

    def read_grid_state() -> dict[str, object]:
        values: list[object] = []
        evaluate_loop = QEventLoop()
        window.view.page().runJavaScript(
            "JSON.stringify({coords: Array.from(document.querySelectorAll('.grid-stack-item'))"
            ".map((item) => { const node = item.gridstackNode || {}; "
            "return [node.x, node.y, node.w, node.h]; }), "
            "height: document.getElementById('widgets-grid').clientHeight, "
            "cell: getComputedStyle(document.getElementById('widgets-grid'))"
            ".getPropertyValue('--gs-cell-height')})",
            lambda value: (values.append(value), evaluate_loop.quit()),
        )
        QTimer.singleShot(5000, evaluate_loop.quit)
        evaluate_loop.exec()
        assert values and isinstance(values[0], str)
        return json.loads(values[0])

    settle_loop = QEventLoop()
    QTimer.singleShot(250, settle_loop.quit)
    settle_loop.exec()
    before = read_grid_state()

    window.resize(760, 620)
    settle_loop = QEventLoop()
    QTimer.singleShot(250, settle_loop.quit)
    settle_loop.exec()
    after = read_grid_state()

    assert before["coords"] == after["coords"]
    assert after["height"] > before["height"]
    assert after["cell"] != before["cell"]
    window.close()
    del app
