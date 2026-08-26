"""Native diagnostics and manual refresh controls for network data."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from deskboard.presentation.data_status_presenter import SourceMetadata
from deskboard.ui.settings.i18n import SUPPORTED_LANGUAGES, translate_text


class DataRefreshServiceLike(Protocol):
    def data_status_rows(self, **kwargs): ...

    def refresh_all(self) -> tuple[str, ...]: ...

    def refresh_group(self, group: str) -> bool: ...


class DataStatusPage(QWidget):
    """Render service-owned diagnostics; no SQL or Provider access lives here."""

    COLUMNS = (
        "Item",
        "Group",
        "Source",
        "Last attempt",
        "Last success",
        "Status",
        "Readable error",
    )

    def __init__(
        self,
        refresh_service: DataRefreshServiceLike | None,
        log_directory: str | Path | None = None,
        *,
        source_metadata: Mapping[str, SourceMetadata] | None = None,
        display_names: Mapping[str, str] | None = None,
        open_log_folder: Callable[[Path], object] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = refresh_service
        self._log_directory = Path(log_directory) if log_directory is not None else None
        self._source_metadata = source_metadata
        self._display_names = display_names
        self._open_log_folder = open_log_folder or _open_folder
        self._language = "zh_CN"
        self._remove_listener: Callable[[], None] | None = None
        self.group_buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        heading = QLabel("Data Status", self)
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(heading)
        intro = QLabel(
            "Network diagnostics and manual refresh. The Dashboard has no refresh controls.",
            self,
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        action_row = QHBoxLayout()
        self.refresh_all_button = QPushButton("Refresh All", self)
        self.refresh_all_button.clicked.connect(self.refresh_all)
        action_row.addWidget(self.refresh_all_button)
        self.open_log_button = QPushButton("Open Log Folder", self)
        self.open_log_button.clicked.connect(self.open_log_folder)
        action_row.addWidget(self.open_log_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)
        self.group_actions = QHBoxLayout()
        layout.addLayout(self.group_actions)
        self.table = QTableWidget(0, len(self.COLUMNS), self)
        self.table.setHorizontalHeaderLabels(list(self.COLUMNS))
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        if refresh_service is not None:
            listener = getattr(refresh_service, "add_listener", None)
            if callable(listener):
                self._remove_listener = listener(lambda _group: self.refresh())
        self.refresh()

    def refresh(self) -> None:
        if self._service is None:
            self.table.setRowCount(0)
            self._clear_group_actions()
            self.status_label.setText(
                translate_text("Data refresh service unavailable", self._language)
            )
            return
        try:
            rows = self._service.data_status_rows(
                source_metadata=self._source_metadata,
                display_names=self._display_names,
            )
        except TypeError:
            rows = self._service.data_status_rows()
        self.table.setRowCount(len(rows))
        for row_number, row in enumerate(rows):
            values = _row_values(row, self._language)
            for column, value in enumerate(values):
                self.table.setItem(row_number, column, QTableWidgetItem(value))
        self._rebuild_group_actions(rows)
        self.status_label.setText(
            (
                f"共 {len(rows)} 个网络项目"
                if self._language == "zh_CN"
                else f"{len(rows)} network items"
            )
        )

    def set_language(self, language: str) -> None:
        if language not in SUPPORTED_LANGUAGES:
            return
        self._language = language
        self.refresh()

    def refresh_all(self) -> tuple[str, ...]:
        if self._service is None:
            return ()
        groups = self._service.refresh_all()
        self.refresh()
        return groups

    def refresh_group(self, group: str) -> bool:
        if self._service is None:
            return False
        started = self._service.refresh_group(group)
        self.refresh()
        return bool(started)

    def open_log_folder(self) -> None:
        if self._log_directory is None:
            self.status_label.setText(
                translate_text("Log folder is unavailable", self._language)
            )
            return
        try:
            self._open_log_folder(self._log_directory)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            self.status_label.setText(
                f"{translate_text('Unable to open log folder', self._language)}: {error}"
            )
        else:
            self.status_label.setText(str(self._log_directory))

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None
        super().closeEvent(event)

    def _clear_group_actions(self) -> None:
        self.group_buttons.clear()
        while self.group_actions.count():
            item = self.group_actions.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

    def _rebuild_group_actions(self, rows: list[Any]) -> None:
        self._clear_group_actions()
        groups: dict[str, bool] = {}
        for row in rows:
            values = _row_mapping(row)
            group = str(values.get("group", ""))
            if group:
                groups[group] = groups.get(group, False) or bool(
                    values.get("refreshAvailable", values.get("refresh_available", False))
                )
        for group in sorted(groups):
            button = QPushButton(
                f"{translate_text('Refresh ', self._language)}"
                f"{_group_label(group, self._language)}",
                self,
            )
            button.setEnabled(groups[group])
            button.clicked.connect(lambda _checked=False, value=group: self.refresh_group(value))
            self.group_buttons[group] = button
            self.group_actions.addWidget(button)
        self.group_actions.addStretch(1)


def _row_values(row: Any, language: str = "zh_CN") -> list[str]:
    values = _row_mapping(row)
    return [
        str(values.get("displayName", values.get("name", values.get("key", "")))),
        _group_label(str(values.get("group", "")), language),
        str(values.get("sourceName", values.get("source", ""))),
        _text_or_dash(values.get("lastAttempt", values.get("last_attempt_at"))),
        _text_or_dash(values.get("lastSuccess", values.get("last_success_at"))),
        translate_text(str(values.get("status", "unknown")), language),
        _text_or_dash(values.get("lastError", values.get("last_error"))),
    ]


def _row_mapping(row: Any) -> dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)
    as_dict = getattr(row, "as_dict", None)
    if callable(as_dict):
        return dict(as_dict())
    return {
        "key": getattr(row, "key", ""),
        "name": getattr(row, "display_name", ""),
        "displayName": getattr(row, "display_name", ""),
        "group": getattr(row, "group", ""),
        "source": getattr(row, "source_name", ""),
        "sourceName": getattr(row, "source_name", ""),
        "status": getattr(row, "status", "unknown"),
        "lastAttempt": getattr(row, "last_attempt_at", None),
        "lastSuccess": getattr(row, "last_success_at", None),
        "lastError": getattr(row, "last_error", None),
        "refreshAvailable": getattr(row, "refresh_available", False),
    }


def _text_or_dash(value: object) -> str:
    if value is None or value == "":
        return "—"
    return str(value)


def _group_label(group: str, language: str = "zh_CN") -> str:
    source = {
        "indices": "China indices",
        "us_indices": "US indices",
        "weather": "Weather",
        "gold": "Gold",
        "fx": "FX",
    }.get(group, group)
    return translate_text(source, language)


def _open_folder(path: Path) -> object:
    if os.name == "nt" and hasattr(os, "startfile"):
        return os.startfile(str(path))  # type: ignore[attr-defined]
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
