"""Current-user Windows autostart integration."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Protocol

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


class RunRegistry(Protocol):
    def get(self, name: str) -> str | None: ...

    def set(self, name: str, command: str) -> None: ...

    def delete(self, name: str) -> None: ...


class _WindowsRunRegistry:
    def __init__(self) -> None:
        import winreg

        self._winreg = winreg

    def get(self, name: str) -> str | None:
        try:
            with self._winreg.OpenKey(self._winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                value, _kind = self._winreg.QueryValueEx(key, name)
        except FileNotFoundError:
            return None
        return str(value)

    def set(self, name: str, command: str) -> None:
        with self._winreg.CreateKey(self._winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            self._winreg.SetValueEx(key, name, 0, self._winreg.REG_SZ, command)

    def delete(self, name: str) -> None:
        try:
            with self._winreg.OpenKey(
                self._winreg.HKEY_CURRENT_USER, RUN_KEY, 0, self._winreg.KEY_SET_VALUE
            ) as key:
                self._winreg.DeleteValue(key, name)
        except FileNotFoundError:
            return


class CurrentUserAutostart:
    """Expose the one supported per-user autostart toggle.

    The registry is deliberately injected in tests.  Construction does not
    write anything, so a new installation remains OFF by default.
    """

    def __init__(
        self,
        app_name: str = "DeskBoard",
        command: str | None = None,
        *,
        registry: RunRegistry | None = None,
        platform_name: str | None = None,
    ) -> None:
        if not isinstance(app_name, str) or not app_name.strip():
            raise ValueError("Autostart application name must not be empty")
        self.app_name = app_name.strip()
        self.command = command or default_autostart_command()
        self._platform_name = platform_name or os.name
        self._registry = registry

    def is_enabled(self) -> bool:
        if self._platform_name != "nt":
            return False
        return self._registry_backend().get(self.app_name) is not None

    def set_enabled(self, enabled: bool) -> None:
        if type(enabled) is not bool:
            raise TypeError("autostart enabled must be a bool")
        if self._platform_name != "nt":
            if enabled:
                raise OSError("DeskBoard autostart is only supported on Windows")
            return
        if enabled:
            self._registry_backend().set(self.app_name, self.command)
        else:
            self._registry_backend().delete(self.app_name)

    def _registry_backend(self) -> RunRegistry:
        if self._registry is None:
            self._registry = _WindowsRunRegistry()
        return self._registry


def default_autostart_command() -> str:
    """Build a current-user Run command for source and packaged launches."""

    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline([sys.executable])
    executable = str(Path(sys.executable).resolve())
    return f"{subprocess.list2cmdline([executable])} -m deskboard"
