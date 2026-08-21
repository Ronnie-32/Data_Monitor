from __future__ import annotations

from datetime import date, datetime

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from deskboard.infrastructure.clock import Clock
from deskboard.models.todo import Todo
from deskboard.ui.dashboard.bridge import DashboardBridge


class FakeClock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 8, 21, 12)

    def today(self) -> date:
        return date(2026, 8, 21)


def _todo() -> Todo:
    timestamp = datetime(2026, 8, 21, 9)
    return Todo(
        id=1,
        content="Delete me",
        deadline_date=None,
        deadline_time=None,
        planned_date=None,
        planned_start_time=None,
        planned_end_time=None,
        completed_at=None,
        display_order=1,
        created_at=timestamp,
        updated_at=timestamp,
    )


class FakeTodoService:
    def get_dashboard_items(self) -> list[Todo]:
        return [_todo()]


def test_real_qwebchannel_invokes_delete_request_slot():
    app = QApplication.instance() or QApplication([])
    view = QWebEngineView()
    bridge = DashboardBridge(todo_service=FakeTodoService(), clock=FakeClock())
    channel = QWebChannel(view.page())
    channel.registerObject("bridge", bridge)
    view.page().setWebChannel(channel)
    requests: list[int] = []
    bridge.todoDeleteRequested.connect(requests.append)

    html = """
    <!doctype html>
    <html><body>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
      new QWebChannel(qt.webChannelTransport, function (channel) {
        channel.objects.bridge.requestDeleteTodo(1);
      });
    </script>
    </body></html>
    """
    loop = QEventLoop()
    bridge.todoDeleteRequested.connect(loop.quit)
    view.setHtml(html)
    QTimer.singleShot(5000, loop.quit)
    loop.exec()

    assert requests == [1]
    view.deleteLater()
    del app
