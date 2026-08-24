"""Finance catalog metadata and global preference values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

FinanceCategory = Literal["gold", "fx", "china_indices", "us_indices"]
FINANCE_CATEGORIES = frozenset({"gold", "fx", "china_indices", "us_indices"})


@dataclass(frozen=True, slots=True)
class FinanceCatalogItem:
    """One code-owned, validated finance item.

    ``key`` is the stable DeskBoard key.  ``provider_internal_key`` is only
    the mapping understood by the selected provider; it is not user input.
    """

    key: str
    display_name: str
    category: FinanceCategory
    unit: str
    value_format: str
    change_format: str
    provider_group: str
    provider_internal_key: str
    source_name: str
    source_homepage: str
    change_percent_format: str = "{:+.2f}%"

    def __post_init__(self) -> None:
        _validate_key(self.key, "Finance catalog key")
        for field_name in (
            "display_name",
            "unit",
            "value_format",
            "change_format",
            "provider_group",
            "provider_internal_key",
            "source_name",
            "source_homepage",
            "change_percent_format",
        ):
            _validate_text(getattr(self, field_name), f"Finance {field_name}")
        if self.category not in FINANCE_CATEGORIES:
            raise ValueError(f"Unsupported finance category: {self.category}")
        parsed = urlparse(self.source_homepage)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Finance source_homepage must be an absolute HTTP(S) URL")

    @property
    def item_key(self) -> str:
        """Database-facing name for the stable item key."""

        return self.key

    @property
    def stable_key(self) -> str:
        """Explicit alias used by catalog consumers."""

        return self.key

    @property
    def provider_key(self) -> str:
        """Short alias for the selected provider's internal mapping."""

        return self.provider_internal_key


@dataclass(frozen=True, slots=True)
class FinancePreference:
    """Persisted global enable/order state for one catalog item."""

    item_key: str
    enabled: bool
    display_order: int

    def __post_init__(self) -> None:
        _validate_key(self.item_key, "Finance preference item key")
        if type(self.enabled) is not bool:
            raise TypeError("Finance preference enabled must be a bool")
        if isinstance(self.display_order, bool) or not isinstance(self.display_order, int):
            raise TypeError("Finance preference display_order must be an integer")
        if self.display_order < 0:
            raise ValueError("Finance preference display_order must not be negative")

    @property
    def key(self) -> str:
        return self.item_key


def _validate_key(value: object, field: str) -> str:
    _validate_text(value, field)
    normalized = value.strip()  # type: ignore[union-attr]
    if any(char.isspace() or char in "/\\" for char in normalized):
        raise ValueError(f"{field} must not contain whitespace or path separators")
    return normalized


def _validate_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value.strip():
        raise ValueError(f"{field} must not be empty")
    return value
