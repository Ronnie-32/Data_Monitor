from pathlib import Path

import pytest

from deskboard.app.single_instance import (
    MAX_PAYLOAD_BYTES,
    SHOW_SETTINGS_COMMAND,
    InstanceRole,
    SingleInstanceGuard,
)


class FakeSignal:
    def __init__(self) -> None:
        self.callbacks = []

    def connect(self, callback) -> None:
        self.callbacks.append(callback)

    def emit(self) -> None:
        for callback in tuple(self.callbacks):
            callback()


class FakeSocket:
    def __init__(
        self,
        *,
        connected: bool,
        write_result: int | None = None,
        write_succeeds: bool = True,
    ) -> None:
        self.connected = connected
        self.write_result = write_result
        self.write_succeeds = write_succeeds
        self.server_names = []
        self.writes = []
        self.wait_for_bytes_calls = []
        self.disconnect_calls = 0

    def connectToServer(self, server_name: str) -> None:  # noqa: N802
        self.server_names.append(server_name)

    def waitForConnected(self, timeout_ms: int) -> bool:  # noqa: N802
        return self.connected

    def write(self, payload: bytes) -> int:
        self.writes.append(payload)
        return len(payload) if self.write_result is None else self.write_result

    def waitForBytesWritten(self, timeout_ms: int) -> bool:  # noqa: N802
        self.wait_for_bytes_calls.append(timeout_ms)
        return self.write_succeeds

    def disconnectFromServer(self) -> None:  # noqa: N802
        self.disconnect_calls += 1


class FakeServer:
    def __init__(self, *, listens=True, server_error=None) -> None:
        self.listen_results = list(listens) if isinstance(listens, list) else [listens]
        self.server_error = server_error
        self.listen_names = []
        self.close_calls = 0
        self.newConnection = FakeSignal()  # noqa: N815
        self.pending_connections = []

    def listen(self, server_name: str) -> bool:
        self.listen_names.append(server_name)
        return self.listen_results.pop(0)

    def serverError(self):  # noqa: N802
        return self.server_error

    def errorString(self) -> str:  # noqa: N802
        return "listen failed"

    def close(self) -> None:
        self.close_calls += 1

    def hasPendingConnections(self) -> bool:  # noqa: N802
        return bool(self.pending_connections)

    def nextPendingConnection(self):  # noqa: N802
        return self.pending_connections.pop(0)


class FakeIncomingSocket:
    def __init__(self, *chunks: bytes) -> None:
        self.chunks = list(chunks)
        self.readyRead = FakeSignal()  # noqa: N815
        self.readChannelFinished = FakeSignal()  # noqa: N815
        self.disconnected = FakeSignal()
        self.disconnect_calls = 0

    def readAll(self) -> bytes:  # noqa: N802
        return self.chunks.pop(0) if self.chunks else b""

    def disconnectFromServer(self) -> None:  # noqa: N802
        self.disconnect_calls += 1


def test_primary_instance_listens_without_sending_a_handoff():
    socket = FakeSocket(connected=False)
    server = FakeServer()
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: None,
        server_factory=lambda: server,
        socket_factory=lambda: socket,
    )

    assert guard.start() is InstanceRole.PRIMARY
    assert server.listen_names == ["DeskBoard.Test"]
    assert len(server.newConnection.callbacks) == 1
    assert socket.writes == []


def test_secondary_sends_show_settings_and_never_starts_a_server():
    socket = FakeSocket(connected=True)
    server = FakeServer()
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: None,
        server_factory=lambda: server,
        socket_factory=lambda: socket,
    )

    assert guard.start() is InstanceRole.SECONDARY
    assert socket.server_names == ["DeskBoard.Test"]
    assert socket.writes == [SHOW_SETTINGS_COMMAND]
    assert socket.disconnect_calls == 1
    assert server.listen_names == []


def test_primary_handoff_command_opens_settings():
    settings_requests = []
    probe = FakeSocket(connected=False)
    server = FakeServer()
    incoming = FakeIncomingSocket(b"show-", b"settings\n")
    server.pending_connections.append(incoming)
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: settings_requests.append(True),
        server_factory=lambda: server,
        socket_factory=lambda: probe,
    )
    assert guard.start() is InstanceRole.PRIMARY

    server.newConnection.emit()
    incoming.readyRead.emit()

    assert settings_requests == []

    incoming.readChannelFinished.emit()

    assert settings_requests == [True]
    assert incoming.disconnect_calls == 1


def test_complete_command_waits_for_channel_end_before_opening_settings():
    settings_requests = []
    probe = FakeSocket(connected=False)
    server = FakeServer()
    incoming = FakeIncomingSocket(SHOW_SETTINGS_COMMAND)
    server.pending_connections.append(incoming)
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: settings_requests.append(True),
        server_factory=lambda: server,
        socket_factory=lambda: probe,
    )
    assert guard.start() is InstanceRole.PRIMARY

    server.newConnection.emit()
    assert settings_requests == []

    incoming.readChannelFinished.emit()
    assert settings_requests == [True]


def test_extra_content_in_later_ready_read_rejects_initially_exact_command():
    settings_requests = []
    probe = FakeSocket(connected=False)
    server = FakeServer()
    incoming = FakeIncomingSocket(SHOW_SETTINGS_COMMAND, b"extra")
    server.pending_connections.append(incoming)
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: settings_requests.append(True),
        server_factory=lambda: server,
        socket_factory=lambda: probe,
    )
    assert guard.start() is InstanceRole.PRIMARY

    server.newConnection.emit()
    assert settings_requests == []
    incoming.readyRead.emit()
    incoming.readChannelFinished.emit()

    assert settings_requests == []
    assert incoming.disconnect_calls == 1


@pytest.mark.parametrize(
    "payload",
    [
        b"unknown\n",
        b"xshow-settings\n",
        b"show-settings\nshow-settings\n",
        b"x" * (MAX_PAYLOAD_BYTES + 1),
    ],
)
def test_primary_rejects_unknown_substring_multiple_and_oversized_commands(payload):
    settings_requests = []
    probe = FakeSocket(connected=False)
    server = FakeServer()
    incoming = FakeIncomingSocket(payload)
    server.pending_connections.append(incoming)
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: settings_requests.append(True),
        server_factory=lambda: server,
        socket_factory=lambda: probe,
    )
    assert guard.start() is InstanceRole.PRIMARY

    server.newConnection.emit()

    assert settings_requests == []
    assert incoming.disconnect_calls == 1


@pytest.mark.parametrize(
    ("write_result", "write_succeeds"),
    [(len(SHOW_SETTINGS_COMMAND) - 1, True), (None, False)],
)
def test_failed_handoff_never_starts_a_second_server(write_result, write_succeeds):
    socket = FakeSocket(
        connected=True,
        write_result=write_result,
        write_succeeds=write_succeeds,
    )
    server_factory_calls = []
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: None,
        server_factory=lambda: server_factory_calls.append(True),
        socket_factory=lambda: socket,
    )

    with pytest.raises(RuntimeError, match="handoff"):
        guard.start()

    assert server_factory_calls == []


def test_address_in_use_race_lost_notifies_winner_without_removing_endpoint():
    address_in_use = object()
    sockets = iter([FakeSocket(connected=False), FakeSocket(connected=True)])
    server = FakeServer(listens=False, server_error=address_in_use)
    removed = []
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: None,
        server_factory=lambda: server,
        socket_factory=lambda: next(sockets),
        address_in_use_error=address_in_use,
        remove_server=lambda name: removed.append(name),
    )

    assert guard.start() is InstanceRole.SECONDARY
    assert server.listen_names == ["DeskBoard.Test"]
    assert removed == []


def test_stale_address_is_removed_once_and_listened_once_more():
    address_in_use = object()
    sockets = iter([FakeSocket(connected=False), FakeSocket(connected=False)])
    server = FakeServer(listens=[False, True], server_error=address_in_use)
    removed = []
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: None,
        server_factory=lambda: server,
        socket_factory=lambda: next(sockets),
        address_in_use_error=address_in_use,
        remove_server=lambda name: removed.append(name),
    )

    assert guard.start() is InstanceRole.PRIMARY
    assert removed == ["DeskBoard.Test"]
    assert server.listen_names == ["DeskBoard.Test", "DeskBoard.Test"]


def test_cleanup_retry_race_lost_performs_one_final_handoff_without_more_cleanup():
    address_in_use = object()
    sockets = iter(
        [
            FakeSocket(connected=False),
            FakeSocket(connected=False),
            FakeSocket(connected=True),
        ]
    )
    server = FakeServer(listens=[False, False], server_error=address_in_use)
    removed = []
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: None,
        server_factory=lambda: server,
        socket_factory=lambda: next(sockets),
        address_in_use_error=address_in_use,
        remove_server=lambda name: removed.append(name),
    )

    assert guard.start() is InstanceRole.SECONDARY
    assert removed == ["DeskBoard.Test"]
    assert server.listen_names == ["DeskBoard.Test", "DeskBoard.Test"]


def test_non_address_listen_error_is_reported_without_retry_or_removal():
    address_in_use = object()
    server = FakeServer(listens=False, server_error=object())
    removed = []
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: None,
        server_factory=lambda: server,
        socket_factory=lambda: FakeSocket(connected=False),
        address_in_use_error=address_in_use,
        remove_server=lambda name: removed.append(name),
    )

    with pytest.raises(RuntimeError, match="listen failed"):
        guard.start()

    assert server.listen_names == ["DeskBoard.Test"]
    assert removed == []


def test_guard_close_is_idempotent():
    socket = FakeSocket(connected=False)
    server = FakeServer()
    guard = SingleInstanceGuard(
        "DeskBoard.Test",
        lambda: None,
        server_factory=lambda: server,
        socket_factory=lambda: socket,
    )
    assert guard.start() is InstanceRole.PRIMARY

    guard.close()
    guard.close()

    assert server.close_calls == 1


def test_main_checks_instance_role_before_creating_application_shell():
    source = Path("src/deskboard/main.py").read_text(encoding="utf-8")

    assert source.index("instance_guard.start()") < source.index(
        "application = DeskBoardApplication("
    )
    assert "instance_guard=instance_guard" in source
