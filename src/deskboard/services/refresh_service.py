"""Low-frequency network refresh, cache, and worker orchestration."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta

from deskboard.infrastructure.clock import Clock
from deskboard.infrastructure.workers import QtThreadPoolExecutor, WorkerExecutor
from deskboard.providers.base import NetworkItem, Provider, ProviderItemResult, ProviderResult
from deskboard.providers.errors import ProviderDataError, ProviderError
from deskboard.repositories.network_repository import NetworkRepository
from deskboard.services.settings_service import SettingsService
from deskboard.services.status_service import StatusService

REFRESH_INTERVAL = timedelta(minutes=60)
REFRESH_INTERVAL_MINUTES = 60


@dataclass(frozen=True, slots=True)
class StartupSnapshot:
    cached_payloads: dict[str, object]
    scheduled_groups: tuple[str, ...]
    status: str

    @property
    def cache(self) -> dict[str, object]:
        return dict(self.cached_payloads)


@dataclass(slots=True)
class _ProviderRegistration:
    group: str
    provider: Provider
    items: tuple[NetworkItem, ...]


class DataRefreshService:
    """Use one shared path for automatic and Settings-triggered refreshes."""

    def __init__(
        self,
        repository: NetworkRepository,
        clock: Clock,
        providers: Mapping[str, Provider] | Iterable[Provider] = (),
        *,
        items: Iterable[NetworkItem | str] | Mapping[str, bool] | None = None,
        worker_executor: WorkerExecutor | None = None,
        status_service: StatusService | None = None,
        settings_service: SettingsService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._settings = settings_service
        self._worker: WorkerExecutor = worker_executor or QtThreadPoolExecutor()
        self._status = status_service or StatusService(repository)
        self._logger = logger or logging.getLogger(__name__)
        self._registrations: dict[str, _ProviderRegistration] = {}
        self._items: dict[str, NetworkItem] = {}
        self._active_groups: set[str] = set()
        self._started = False
        self._next_refresh_at: datetime | None = None
        self._dashboard_visible = True
        self._listeners: list[Callable[[str], None]] = []
        global_items = _normalize_items(items) if items is not None else None
        self._register_initial_providers(providers, global_items)
        self._status.configure_items(tuple(self._items.values()))

    @property
    def status_service(self) -> StatusService:
        return self._status

    @property
    def network_items(self) -> tuple[NetworkItem, ...]:
        """Return the globally configured items for Settings diagnostics."""

        return tuple(self._items.values())

    @property
    def groups(self) -> tuple[str, ...]:
        """Return provider groups that can be refreshed from Settings."""

        return tuple(sorted(self._registrations))

    def data_status_rows(
        self,
        *,
        source_metadata=None,
        display_names=None,
    ):
        """Build Data Status rows through the presentation boundary."""

        from deskboard.presentation.data_status_presenter import present_data_status

        return present_data_status(
            self.network_items,
            self._repository,
            source_metadata=source_metadata,
            display_names=display_names,
            active_groups=self.active_groups,
        )

    @property
    def refresh_interval(self) -> timedelta:
        return REFRESH_INTERVAL

    @property
    def active_groups(self) -> tuple[str, ...]:
        return tuple(sorted(self._active_groups))

    @property
    def next_refresh_at(self) -> datetime | None:
        return self._next_refresh_at

    def register_provider(
        self,
        provider: Provider,
        *,
        items: Iterable[NetworkItem | str] | None = None,
    ) -> None:
        group = _provider_group(provider)
        selected = _normalize_items(items) if items is not None else ()
        if not selected:
            selected = tuple(
                item
                for item in self._items.values()
                if item.group == group
            )
        if not selected:
            selected = (NetworkItem(group, group),)
        normalized = tuple(
            NetworkItem(item.key, group, self._effective_enabled(item)) for item in selected
        )
        self._registrations[group] = _ProviderRegistration(group, provider, normalized)
        self._items.update({item.key: item for item in normalized})
        self._status.configure_items(tuple(self._items.values()))

    def replace_provider(
        self,
        provider: Provider,
        *,
        items: Iterable[NetworkItem | str] | None = None,
    ) -> None:
        """Reconcile one provider group's runtime item catalog.

        This is used for global catalogs such as Weather cities, which can be
        edited while DeskBoard is running.  Stale items are removed from the
        refresh/status view so a newly added item becomes part of the same
        provider group immediately.
        """

        group = _provider_group(provider)
        selected = (
            _normalize_items(items)
            if items is not None
            else _normalize_items(getattr(provider, "items", ()))
        )
        normalized = tuple(
            NetworkItem(item.key, group, self._effective_enabled(item)) for item in selected
        )
        self._registrations[group] = _ProviderRegistration(group, provider, normalized)
        self._items = {
            key: item for key, item in self._items.items() if str(item.group) != group
        }
        self._items.update({item.key: item for item in normalized})
        self._status.configure_items(tuple(self._items.values()))

    def set_dashboard_visible(self, visible: bool) -> None:
        """Record visibility for callers without making it a scheduling input."""

        if type(visible) is not bool:
            raise TypeError("dashboard visibility must be a bool")
        self._dashboard_visible = visible

    @property
    def dashboard_visible(self) -> bool:
        return self._dashboard_visible

    def add_listener(self, listener: Callable[[str], None]) -> Callable[[], None]:
        if not callable(listener):
            raise TypeError("refresh listener must be callable")
        self._listeners.append(listener)

        def remove() -> None:
            try:
                self._listeners.remove(listener)
            except ValueError:
                pass

        return remove

    subscribe = add_listener

    def startup(self) -> StartupSnapshot:
        if self._started:
            return self._snapshot(())
        self._started = True
        now = self._clock.now()
        self._next_refresh_at = now + REFRESH_INTERVAL
        cached_payloads: dict[str, object] = {}
        stale_groups: set[str] = set()
        for item in self._items.values():
            cache = self._repository.get_cache(item.key)
            if cache is not None:
                cached_payloads[item.key] = cache.payload
            if not item.enabled:
                continue
            if cache is None or now - cache.success_at >= REFRESH_INTERVAL:
                if item.group in self._registrations:
                    stale_groups.add(str(item.group))
        scheduled = tuple(
            group
            for group in sorted(stale_groups)
            if self.refresh_group(group, reason="startup")
        )
        return StartupSnapshot(cached_payloads, scheduled, self._status.color)

    start = startup

    def refresh_due(self) -> tuple[str, ...]:
        if not self._started:
            self.startup()
        now = self._clock.now()
        if self._next_refresh_at is None or now < self._next_refresh_at:
            return ()
        self._next_refresh_at = now + REFRESH_INTERVAL
        return self.refresh_all(reason="automatic")

    tick = refresh_due

    def refresh_all(self, *, reason: str = "manual") -> tuple[str, ...]:
        del reason  # Manual and automatic requests intentionally share one path.
        return tuple(
            group
            for group in sorted(self._registrations)
            if self.refresh_group(group)
        )

    def refresh_group(self, group: str, *, reason: str = "manual") -> bool:
        del reason
        registration = self._registrations.get(group)
        if registration is None or group in self._active_groups:
            return False
        enabled_items = tuple(item for item in registration.items if item.enabled)
        if not enabled_items:
            return False
        self._active_groups.add(group)
        self._status.begin_refresh(group)
        try:
            self._worker.submit(
                registration.provider.fetch,
                lambda result, selected_group=group: self._complete_success(
                    selected_group, result
                ),
                lambda error, selected_group=group: self._complete_failure(
                    selected_group, error
                ),
            )
        except BaseException as error:  # noqa: BLE001 - executor failure is a refresh failure
            self._complete_failure(group, error)
        return True

    def read_cached_payload(self, cache_key: str) -> object | None:
        cache = self._repository.get_cache(cache_key)
        return None if cache is None else cache.payload

    def _complete_success(self, group: str, result: object) -> None:
        registration = self._registrations[group]
        try:
            outcomes = self._coerce_result(registration, result)
            now = self._clock.now()
            for outcome in outcomes:
                item = self._items.get(outcome.key)
                if item is None or item.group != group or not item.enabled:
                    continue
                if outcome.ok:
                    self._repository.save_success(item.key, outcome.payload, now)
                else:
                    self._repository.record_failure(
                        item.key,
                        now,
                        _error_summary(outcome.error),
                    )
        except BaseException as error:  # noqa: BLE001 - malformed provider result is a failed group
            self._complete_failure(group, error)
            return
        self._finish_group(group)

    def _complete_failure(self, group: str, error: BaseException) -> None:
        registration = self._registrations[group]
        now = self._clock.now()
        summary = _error_summary(error)
        for item in registration.items:
            if item.enabled:
                self._repository.record_failure(item.key, now, summary)
        self._logger.warning("Network provider group %s failed: %s", group, summary)
        self._finish_group(group)

    def _finish_group(self, group: str) -> None:
        self._active_groups.discard(group)
        self._status.end_refresh(group)
        for listener in tuple(self._listeners):
            try:
                listener(group)
            except Exception:  # noqa: BLE001 - observers must not break refresh
                self._logger.exception("Refresh listener failed for group %s", group)

    def _snapshot(self, scheduled_groups: tuple[str, ...]) -> StartupSnapshot:
        cached_payloads = {
            item.key: cache.payload
            for item in self._items.values()
            if (cache := self._repository.get_cache(item.key)) is not None
        }
        return StartupSnapshot(cached_payloads, scheduled_groups, self._status.color)

    def _register_initial_providers(
        self,
        providers: Mapping[str, Provider] | Iterable[Provider],
        global_items: tuple[NetworkItem, ...] | None,
    ) -> None:
        if isinstance(providers, Mapping):
            provider_entries = tuple(providers.items())
        else:
            provider_entries = tuple((None, provider) for provider in providers)
        global_by_group: dict[str, list[NetworkItem]] = {}
        if global_items is not None:
            for item in global_items:
                global_by_group.setdefault(str(item.group), []).append(item)
            self._items.update({item.key: item for item in global_items})
        for fallback_group, provider in provider_entries:
            group = _provider_group(provider, fallback_group)
            selected = tuple(global_by_group.get(group, ()))
            if not selected:
                provider_items = getattr(provider, "items", ())
                selected = _normalize_items(provider_items) if provider_items else ()
            self.register_provider(provider, items=selected or None)

    def _effective_enabled(self, item: NetworkItem) -> bool:
        if self._settings is None:
            return item.enabled
        return item.enabled and self._settings.is_network_item_enabled(item.key, default=True)

    def _coerce_result(
        self,
        registration: _ProviderRegistration,
        result: object,
    ) -> tuple[ProviderItemResult, ...]:
        enabled_items = tuple(item for item in registration.items if item.enabled)
        if isinstance(result, ProviderResult):
            if not result.items:
                raise ProviderDataError("provider returned no normalized items")
            return tuple(
                _map_outcome_key(outcome, enabled_items) for outcome in result.items
            )
        if isinstance(result, ProviderItemResult):
            return (_map_outcome_key(result, enabled_items),)
        if isinstance(result, Mapping) and len(enabled_items) > 1:
            keys = {item.key for item in enabled_items}
            if set(result).issubset(keys):
                if not result:
                    raise ProviderDataError("provider returned no normalized items")
                return tuple(
                    ProviderItemResult.success(key, result[key]) for key in result
                )
        target = enabled_items[0].key
        return (ProviderItemResult.success(target, result),)


def _provider_group(provider: Provider, fallback: str | None = None) -> str:
    value = getattr(provider, "group", None) or getattr(provider, "provider_group", None)
    value = value or fallback
    if not isinstance(value, str) or not value.strip():
        raise ValueError("provider group must not be empty")
    return value.strip()


def _normalize_items(
    items: Iterable[NetworkItem | str] | Mapping[str, bool],
) -> tuple[NetworkItem, ...]:
    if isinstance(items, Mapping):
        return tuple(NetworkItem(str(key), str(key), bool(value)) for key, value in items.items())
    normalized: list[NetworkItem] = []
    for item in items:
        normalized.append(item if isinstance(item, NetworkItem) else NetworkItem(item, item))
    return tuple(normalized)


def _map_outcome_key(
    outcome: ProviderItemResult,
    enabled_items: tuple[NetworkItem, ...],
) -> ProviderItemResult:
    if outcome.key in {item.key for item in enabled_items} or len(enabled_items) != 1:
        return outcome
    return ProviderItemResult(
        key=enabled_items[0].key,
        payload=outcome.payload,
        ok=outcome.ok,
        error=outcome.error,
    )


def _error_summary(error: BaseException | str | None) -> str:
    if isinstance(error, ProviderError):
        message = error.user_message
    elif isinstance(error, BaseException):
        message = str(error) or error.__class__.__name__
    else:
        message = str(error) if error is not None else "provider failed"
    normalized = message.strip()
    return normalized or "provider failed"
