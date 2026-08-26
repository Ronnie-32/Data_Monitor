from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QTimer

from deskboard.infrastructure.workers import QtThreadPoolExecutor


def test_qt_thread_pool_delivers_all_completion_callbacks():
    app = QCoreApplication.instance() or QCoreApplication([])
    completed: list[int] = []
    errors: list[BaseException] = []
    executor = QtThreadPoolExecutor()

    for value in range(8):
        executor.submit(
            lambda value=value: value,
            completed.append,
            errors.append,
        )

    QTimer.singleShot(1_000, app.quit)
    app.exec()

    assert sorted(completed) == list(range(8))
    assert errors == []
