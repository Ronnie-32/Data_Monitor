"""Business rules for the global Finance catalog preferences."""

from __future__ import annotations

from collections.abc import Iterable

from deskboard.models.finance import FinanceCatalogItem, FinancePreference
from deskboard.providers.base import NetworkItem
from deskboard.providers.catalog import DEFAULT_FINANCE_CATALOG, FinanceCatalog
from deskboard.repositories.finance_repository import FinanceRepository


class FinanceService:
    """Validate catalog membership and keep finance choices Profile-independent."""

    def __init__(
        self,
        repository: FinanceRepository,
        catalog: FinanceCatalog | None = None,
    ) -> None:
        self._repository = repository
        self._catalog = catalog or DEFAULT_FINANCE_CATALOG
        self._ensure_initial_configuration()

    @property
    def repository(self) -> FinanceRepository:
        return self._repository

    @property
    def catalog(self) -> FinanceCatalog:
        return self._catalog

    def catalog_items(self) -> tuple[FinanceCatalogItem, ...]:
        return self._catalog.items

    def get_catalog_item(self, item_key: str) -> FinanceCatalogItem | None:
        return self._catalog.get(item_key)

    def require_catalog_item(self, item_key: str) -> FinanceCatalogItem:
        return self._catalog.require(item_key)

    def list_preferences(self) -> list[FinancePreference]:
        allowed = set(self._catalog.keys)
        return [
            preference
            for preference in self._repository.list_preferences()
            if preference.item_key in allowed
        ]

    preferences = list_preferences

    def ordered_items(self) -> list[FinanceCatalogItem]:
        by_key = {item.key: item for item in self._catalog}
        return [by_key[preference.item_key] for preference in self.list_preferences()]

    def enabled_items(self) -> list[FinanceCatalogItem]:
        enabled = {
            preference.item_key
            for preference in self.list_preferences()
            if preference.enabled
        }
        return [item for item in self.ordered_items() if item.key in enabled]

    list_enabled_items = enabled_items

    def get_preference(self, item_key: str) -> FinancePreference:
        self._require_catalog_key(item_key)
        preference = next(
            (
                item
                for item in self.list_preferences()
                if item.item_key == item_key.strip()
            ),
            None,
        )
        if preference is None:
            raise LookupError(f"Finance preference {item_key} does not exist")
        return preference

    def is_enabled(self, item_key: str) -> bool:
        return self.get_preference(item_key).enabled

    def set_enabled(self, item_key: str, enabled: bool) -> FinancePreference:
        key = self._require_catalog_key(item_key)
        return self._repository.set_enabled(key, enabled)

    def enable(self, item_key: str) -> FinancePreference:
        return self.set_enabled(item_key, True)

    def disable(self, item_key: str) -> FinancePreference:
        return self.set_enabled(item_key, False)

    def reorder(self, ordered_keys: Iterable[str]) -> list[FinancePreference]:
        keys = _validated_keys(ordered_keys)
        preferences = self.list_preferences()
        current_keys = tuple(preference.item_key for preference in preferences)
        enabled_keys = tuple(
            preference.item_key for preference in preferences if preference.enabled
        )
        if set(keys) == set(current_keys) and len(keys) == len(current_keys):
            repository_keys = keys
        elif set(keys) == set(enabled_keys) and len(keys) == len(enabled_keys):
            disabled_keys = tuple(
                preference.item_key for preference in preferences if not preference.enabled
            )
            repository_keys = keys + disabled_keys
        else:
            raise ValueError(
                "Finance reorder must contain exactly all catalog keys or all enabled keys"
            )
        return self._repository.reorder(repository_keys)

    reorder_items = reorder
    reorder_enabled = reorder

    def network_items(self) -> tuple[NetworkItem, ...]:
        preferences = {item.item_key: item for item in self.list_preferences()}
        return tuple(
            NetworkItem(
                item.key,
                item.provider_group,
                preferences[item.key].enabled,
            )
            for item in self.ordered_items()
        )

    def enabled_network_items(self) -> tuple[NetworkItem, ...]:
        return tuple(item for item in self.network_items() if item.enabled)

    def _ensure_initial_configuration(self) -> None:
        self._repository.ensure_items(self._catalog.keys)

    def _require_catalog_key(self, item_key: str) -> str:
        return self._catalog.require(item_key).key


def _validated_keys(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("Finance reorder keys must be an iterable of strings")
    keys: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise TypeError("Finance reorder keys must be strings")
        normalized = value.strip()
        if not normalized:
            raise ValueError("Finance reorder keys must not be empty")
        keys.append(normalized)
    if len(keys) != len(set(keys)):
        raise ValueError("Finance reorder keys must be unique")
    return tuple(keys)
