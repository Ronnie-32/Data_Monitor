"""Present persisted network diagnostics for the native Data Status page."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from deskboard.providers.base import NetworkItem
from deskboard.repositories.network_repository import NetworkRepository

DataStatus = Literal["disabled", "never", "refreshing", "success", "error"]


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    """Human-readable attribution for one provider group or item."""

    name: str
    homepage: str

    @property
    def source_name(self) -> str:
        return self.name

    @property
    def source_url(self) -> str:
        return self.homepage


@dataclass(frozen=True, slots=True)
class DataStatusRow:
    """One JSON-friendly diagnostic row without exposing repository objects."""

    key: str
    display_name: str
    group: str
    source_name: str
    source_url: str
    enabled: bool
    status: DataStatus
    last_attempt_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    refresh_available: bool

    @property
    def source(self) -> str:
        return self.source_name

    @property
    def error(self) -> str | None:
        return self.last_error

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "name": self.display_name,
            "displayName": self.display_name,
            "group": self.group,
            "source": self.source_name,
            "sourceName": self.source_name,
            "sourceUrl": self.source_url,
            "attribution": {"name": self.source_name, "url": self.source_url},
            "enabled": self.enabled,
            "status": self.status,
            "lastAttempt": _datetime_text(self.last_attempt_at),
            "lastSuccess": _datetime_text(self.last_success_at),
            "lastError": self.last_error,
            "error": self.last_error,
            "refreshAvailable": self.refresh_available,
            "refreshGroup": self.group,
        }


DEFAULT_SOURCE_METADATA = {
    "weather": SourceMetadata("中国天气网", "https://www.weather.com.cn/"),
    "gold": SourceMetadata("上海黄金交易所", "https://www.sge.com.cn/"),
    "fx": SourceMetadata("中国外汇交易中心", "https://www.chinamoney.com.cn/"),
    "indices": SourceMetadata("腾讯行情", "https://finance.qq.com/"),
    "china_indices": SourceMetadata("腾讯行情", "https://finance.qq.com/"),
    "us_indices": SourceMetadata("腾讯行情", "https://finance.qq.com/"),
}


def present_data_status(
    items: Iterable[NetworkItem],
    repository: NetworkRepository,
    *,
    source_metadata: Mapping[str, SourceMetadata] | None = None,
    display_names: Mapping[str, str] | None = None,
    active_groups: Iterable[str] = (),
) -> list[DataStatusRow]:
    """Join network config, last attempt state, cache success, and attribution.

    ``items`` and ``repository`` are supplied by the application service.  The
    native page consumes the resulting rows and never queries SQLite itself.
    Metadata may be keyed by either an item key or its provider group.
    """

    metadata = dict(DEFAULT_SOURCE_METADATA)
    if source_metadata:
        metadata.update(source_metadata)
    names = display_names or {}
    active = {str(group) for group in active_groups}
    rows: list[DataStatusRow] = []
    for item in items:
        group = str(item.group)
        attribution = metadata.get(item.key) or metadata.get(group)
        if attribution is None:
            attribution = SourceMetadata(group, "")
        state = repository.get_state(item.key)
        cache = repository.get_cache(item.key)
        if not item.enabled:
            status: DataStatus = "disabled"
        elif group in active:
            status = "refreshing"
        elif state is None or state.last_status == "never":
            status = "never"
        else:
            status = state.last_status
        rows.append(
            DataStatusRow(
                key=item.key,
                display_name=names.get(item.key, item.key),
                group=group,
                source_name=attribution.name,
                source_url=attribution.homepage,
                enabled=item.enabled,
                status=status,
                last_attempt_at=None if state is None else state.last_attempt_at,
                last_success_at=None if cache is None else cache.success_at,
                last_error=None if state is None else state.last_error_summary,
                refresh_available=item.enabled and group not in active,
            )
        )
    return rows


present_data_status_rows = present_data_status
build_data_status_rows = present_data_status


def _datetime_text(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()
