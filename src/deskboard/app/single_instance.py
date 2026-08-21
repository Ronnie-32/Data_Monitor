"""One-instance local IPC guard for the DeskBoard application shell."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any

SHOW_SETTINGS_COMMAND = b"show-settings\n"
MAX_PAYLOAD_BYTES = 64
CONNECT_TIMEOUT_MS = 250
WRITE_TIMEOUT_MS = 500


class InstanceRole(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class SingleInstanceGuard:
    """Own a QLocalServer or notify the process that already owns it."""

    def __init__(
        self,
        server_name: str,
        show_settings: Callable[[], None],
        *,
        server_factory: Callable[[], Any] | None = None,
        socket_factory: Callable[[], Any] | None = None,
        address_in_use_error: Any | None = None,
        remove_server: Callable[[str], Any] | None = None,
    ) -> None:
        if not server_name:
            raise ValueError("server_name must not be empty")
        self.server_name = server_name
        self._show_settings = show_settings
        self._server_factory = server_factory or self._default_server_factory
        self._socket_factory = socket_factory or self._default_socket_factory
        self._address_in_use_error = (
            address_in_use_error
            if address_in_use_error is not None
            else self._default_address_in_use_error()
        )
        self._remove_server = remove_server or self._default_remove_server
        self._server: Any | None = None
        self._connections: list[Any] = []
        self._buffers: dict[int, bytes] = {}
        self._closed = False

    @staticmethod
    def _default_server_factory() -> Any:
        from PySide6.QtNetwork import QLocalServer

        return QLocalServer()

    @staticmethod
    def _default_socket_factory() -> Any:
        from PySide6.QtNetwork import QLocalSocket

        return QLocalSocket()

    @staticmethod
    def _default_address_in_use_error() -> Any:
        from PySide6.QtNetwork import QAbstractSocket

        return QAbstractSocket.SocketError.AddressInUseError

    @staticmethod
    def _default_remove_server(server_name: str) -> bool:
        from PySide6.QtNetwork import QLocalServer

        return QLocalServer.removeServer(server_name)

    def start(self) -> InstanceRole:
        """Become primary, or send the handoff and identify as secondary."""
        if self._notify_existing():
            return InstanceRole.SECONDARY

        self._server = self._server_factory()
        self._server.newConnection.connect(self._accept_pending_connections)
        if self._server.listen(self.server_name):
            return InstanceRole.PRIMARY

        if self._server.serverError() == self._address_in_use_error:
            # Another process may have won the listen race after the first probe.
            if self._notify_existing():
                return InstanceRole.SECONDARY
            # One bounded stale-endpoint recovery; never remove a confirmed primary.
            self._remove_server(self.server_name)
            if self._server.listen(self.server_name):
                return InstanceRole.PRIMARY
            if (
                self._server.serverError() == self._address_in_use_error
                and self._notify_existing()
            ):
                return InstanceRole.SECONDARY
        raise RuntimeError(
            "Unable to establish single-instance server: "
            f"{self._server.errorString()}"
        )

    def _notify_existing(self) -> bool:
        socket = self._socket_factory()
        socket.connectToServer(self.server_name)
        if not socket.waitForConnected(CONNECT_TIMEOUT_MS):
            return False
        written = socket.write(SHOW_SETTINGS_COMMAND)
        if written != len(SHOW_SETTINGS_COMMAND):
            socket.disconnectFromServer()
            raise RuntimeError("Single-instance handoff write was incomplete")
        if not socket.waitForBytesWritten(WRITE_TIMEOUT_MS):
            socket.disconnectFromServer()
            raise RuntimeError("Single-instance handoff write timed out")
        socket.disconnectFromServer()
        return True

    def _accept_pending_connections(self) -> None:
        if self._server is None:
            return
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            self._connections.append(socket)
            self._buffers[id(socket)] = b""
            socket.readyRead.connect(lambda current=socket: self._read_available(current))
            socket.readChannelFinished.connect(
                lambda current=socket: self._finish_command(current)
            )
            socket.disconnected.connect(
                lambda current=socket: self._finish_command(current)
            )
            self._read_available(socket)

    def _read_available(self, socket: Any) -> None:
        key = id(socket)
        if key not in self._buffers:
            return
        payload = self._buffers.get(key, b"") + bytes(socket.readAll())
        if len(payload) > MAX_PAYLOAD_BYTES or not SHOW_SETTINGS_COMMAND.startswith(
            payload
        ):
            self._discard_connection(socket)
            socket.disconnectFromServer()
            return
        self._buffers[key] = payload

    def _finish_command(self, socket: Any) -> None:
        key = id(socket)
        if key not in self._buffers:
            return
        self._read_available(socket)
        if key not in self._buffers:
            return
        payload = self._buffers[key]
        self._discard_connection(socket)
        if not self._closed and payload == SHOW_SETTINGS_COMMAND:
            self._show_settings()
        socket.disconnectFromServer()

    def _discard_connection(self, socket: Any) -> None:
        self._buffers.pop(id(socket), None)
        if socket in self._connections:
            self._connections.remove(socket)

    def close(self) -> None:
        """Release the primary endpoint and accepted sockets exactly once."""
        if self._closed:
            return
        self._closed = True
        for socket in tuple(self._connections):
            socket.disconnectFromServer()
        self._connections.clear()
        self._buffers.clear()
        if self._server is not None:
            self._server.close()
