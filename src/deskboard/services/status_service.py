"""Derived global network status, independent of Profile visibility."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal

from deskboard.providers.base import NetworkItem
from deskboard.repositories.network_repository import NetworkRepository

StatusColor = Literal["grey", "green", "red"]


@dataclass(frozen=True, slots=True)
class NetworkStatusSnapshot:
    color: StatusColor
    enabled_keys: tuple[str, ...]
    active_groups: tuple[str, ...]


class StatusService:
    """Derive one global grey/green/red state from enabled network items."""

    def __init__(
        self,
        repository: NetworkRepository,
        *,
        items: Iterable[NetworkItem | str] | Mapping[str, bool] = (),
    ) -> None:
        self._repository = repository
        self._items: dict[str, NetworkItem] = {}
        self._active_groups: set[str] = set()
        self.configure_items(items)

    @property
    def color(self) -> StatusColor:
        enabled = [item for item in self._items.values() if item.enabled]
        if not enabled:
            return "grey"
        if any(
            group in self._active_groups
            for group in {str(item.group) for item in enabled}
        ):
            return "grey"
        states = [self._repository.get_state(item.key) for item in enabled]
        if any(state is not None and state.last_status == "error" for state in states):
            return "red"
        if any(state is None or state.last_status == "never" for state in states):
            return "grey"
        return "green"

    @property
    def status(self) -> StatusColor:
        return self.color

    def get_color(self) -> StatusColor:
        return self.color

    def configure_items(
        self,
        items: Iterable[NetworkItem | str] | Mapping[str, bool],
    ) -> None:
        self._items = {
            item.key: item for item in _normalize_items(items)
        }
        self._active_groups.intersection_update({str(item.group) for item in self._items.values()})

    set_enabled_items = configure_items

    def set_item_enabled(self, item_key: str, enabled: bool) -> None:
        current = self._items.get(item_key)
        if current is None:
            self._items[item_key] = NetworkItem(item_key, item_key, enabled)
        else:
            self._items[item_key] = NetworkItem(current.key, current.group, enabled)

    def begin_refresh(self, group: str) -> None:
        if not isinstance(group, str) or not group.strip():
            raise ValueError("network provider group must not be empty")
        if any(item.enabled and item.group == group for item in self._items.values()):
            self._active_groups.add(group)

    def end_refresh(self, group: str) -> None:
        self._active_groups.discard(group)

    @property
    def active_groups(self) -> tuple[str, ...]:
        return tuple(sorted(self._active_groups))

    @property
    def enabled_items(self) -> tuple[NetworkItem, ...]:
        return tuple(item for item in self._items.values() if item.enabled)

    def snapshot(self) -> NetworkStatusSnapshot:
        return NetworkStatusSnapshot(
            color=self.color,
            enabled_keys=tuple(item.key for item in self.enabled_items),
            active_groups=self.active_groups,
        )


def _normalize_items(
    items: Iterable[NetworkItem | str] | Mapping[str, bool],
) -> tuple[NetworkItem, ...]:
    if isinstance(items, Mapping):
        return tuple(
            NetworkItem(str(key), str(key), bool(enabled))
            for key, enabled in items.items()
        )
    normalized: list[NetworkItem] = []
    for item in items:
        normalized.append(item if isinstance(item, NetworkItem) else NetworkItem(item, item))
    return tuple(normalized)
