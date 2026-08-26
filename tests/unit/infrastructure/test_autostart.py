from deskboard.infrastructure.autostart import CurrentUserAutostart


class FakeRunRegistry:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, name: str) -> str | None:
        return self.values.get(name)

    def set(self, name: str, command: str) -> None:
        self.values[name] = command

    def delete(self, name: str) -> None:
        self.values.pop(name, None)


def test_current_user_autostart_defaults_off_and_writes_only_when_enabled():
    registry = FakeRunRegistry()
    autostart = CurrentUserAutostart(
        command='"DeskBoard.exe"',
        registry=registry,
        platform_name="nt",
    )

    assert autostart.is_enabled() is False

    autostart.set_enabled(True)
    assert autostart.is_enabled() is True
    assert registry.values == {"DeskBoard": '"DeskBoard.exe"'}

    autostart.set_enabled(False)
    assert autostart.is_enabled() is False
    assert registry.values == {}


def test_current_user_autostart_is_disabled_on_non_windows_without_registry_access():
    registry = FakeRunRegistry()
    autostart = CurrentUserAutostart(
        command='"DeskBoard"',
        registry=registry,
        platform_name="posix",
    )

    assert autostart.is_enabled() is False
    autostart.set_enabled(False)
    assert registry.values == {}
