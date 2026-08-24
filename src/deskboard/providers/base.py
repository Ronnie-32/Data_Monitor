"""Provider-facing normalized result contracts.

Providers return these values to the refresh layer.  They do not know about
SQLite, UI objects, global status, or retry scheduling.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class NetworkItem:
    """One globally configured network item and its provider group."""

    key: str
    group: str | None = None
    enabled: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key.strip():
            raise ValueError("network item key must not be empty")
        if self.group is None:
            object.__setattr__(self, "group", self.key)
        elif not isinstance(self.group, str) or not self.group.strip():
            raise ValueError("network item group must not be empty")
        if type(self.enabled) is not bool:
            raise TypeError("network item enabled must be a bool")


@dataclass(frozen=True, slots=True)
class ProviderItemResult:
    """Success or failure for one normalized item in a provider response."""

    key: str
    payload: Any = None
    ok: bool = True
    error: BaseException | str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key.strip():
            raise ValueError("provider result key must not be empty")
        if self.ok and self.error is not None:
            raise ValueError("successful provider result cannot contain an error")
        if not self.ok and self.error is None:
            raise ValueError("failed provider result must contain an error")

    @property
    def is_success(self) -> bool:
        return self.ok

    @classmethod
    def success(cls, key: str, payload: Any) -> "ProviderItemResult":
        return cls(key=key, payload=payload, ok=True)

    @classmethod
    def failure(
        cls, key: str, error: BaseException | str
    ) -> "ProviderItemResult":
        return cls(key=key, ok=False, error=error)


@dataclass(frozen=True, slots=True)
class ProviderResult:
    """A provider response that may contain independent item outcomes."""

    items: tuple[ProviderItemResult, ...]

    def __post_init__(self) -> None:
        normalized = tuple(self.items)
        if any(not isinstance(item, ProviderItemResult) for item in normalized):
            raise TypeError("provider result items must be ProviderItemResult values")
        keys = [item.key for item in normalized]
        if len(keys) != len(set(keys)):
            raise ValueError("provider result item keys must be unique")
        object.__setattr__(self, "items", normalized)

    @classmethod
    def success(cls, key: str, payload: Any) -> "ProviderResult":
        return cls((ProviderItemResult.success(key, payload),))

    @classmethod
    def failure(
        cls, key: str, error: BaseException | str
    ) -> "ProviderResult":
        return cls((ProviderItemResult.failure(key, error),))

    @classmethod
    def partial(
        cls, items: tuple[ProviderItemResult, ...] | list[ProviderItemResult]
    ) -> "ProviderResult":
        return cls(tuple(items))

    @property
    def successful_items(self) -> tuple[ProviderItemResult, ...]:
        return tuple(item for item in self.items if item.ok)

    @property
    def failed_items(self) -> tuple[ProviderItemResult, ...]:
        return tuple(item for item in self.items if not item.ok)


class Provider(Protocol):
    """Minimal provider contract used by ``DataRefreshService``."""

    group: str

    def fetch(self) -> ProviderResult | Mapping[str, Any] | Any: ...


BaseProvider = Provider
