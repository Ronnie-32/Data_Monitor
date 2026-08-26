"""Small QThreadPool/QRunnable worker boundary.

Only the provider fetch function runs in the worker.  Repository writes and
status derivation happen in the completion callback on the receiver side.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal

ResultT = TypeVar("ResultT")


class WorkerExecutor(Protocol):
    def submit(
        self,
        job: Callable[[], ResultT],
        on_success: Callable[[ResultT], None],
        on_error: Callable[[BaseException], None],
    ) -> object: ...


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(object)
    finished = Signal()


class _FunctionRunnable(QRunnable):
    def __init__(self, job: Callable[[], Any]) -> None:
        super().__init__()
        self.job = job
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            self.signals.result.emit(self.job())
        except BaseException as error:  # noqa: BLE001 - propagate provider failures
            self.signals.error.emit(error)
        finally:
            self.signals.finished.emit()


class QtThreadPoolExecutor:
    """Submit bounded provider work to Qt's thread pool."""

    def __init__(self, pool: QThreadPool | None = None) -> None:
        self._pool = pool or QThreadPool.globalInstance()
        self._runnables: dict[int, _FunctionRunnable] = {}

    @property
    def pool(self) -> QThreadPool:
        return self._pool

    def submit(
        self,
        job: Callable[[], ResultT],
        on_success: Callable[[ResultT], None],
        on_error: Callable[[BaseException], None],
    ) -> _FunctionRunnable:
        runnable = _FunctionRunnable(job)
        runnable.setAutoDelete(False)
        runnable.signals.result.connect(on_success, Qt.ConnectionType.QueuedConnection)
        runnable.signals.error.connect(on_error, Qt.ConnectionType.QueuedConnection)
        runnable_id = id(runnable)
        self._runnables[runnable_id] = runnable
        runnable.signals.finished.connect(
            lambda selected_id=runnable_id: self._release(selected_id),
            Qt.ConnectionType.QueuedConnection,
        )
        try:
            self._pool.start(runnable)
        except BaseException:
            self._runnables.pop(runnable_id, None)
            raise
        return runnable

    def _release(self, runnable_id: int) -> None:
        self._runnables.pop(runnable_id, None)


class SynchronousWorkerExecutor:
    """Deterministic executor useful for service-level tests and tooling."""

    def submit(
        self,
        job: Callable[[], ResultT],
        on_success: Callable[[ResultT], None],
        on_error: Callable[[BaseException], None],
    ) -> object:
        try:
            on_success(job())
        except BaseException as error:  # noqa: BLE001 - match worker behavior
            on_error(error)
        return object()


# Descriptive aliases for callers that name the implementation by its Qt type.
QThreadPoolWorkerExecutor = QtThreadPoolExecutor
ThreadPoolWorkerExecutor = QtThreadPoolExecutor
