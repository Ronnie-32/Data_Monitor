"""Native global Finance whitelist/order Settings page."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from deskboard.ui.settings.i18n import SUPPORTED_LANGUAGES, translate_text


class FinancePage(QWidget):
    def __init__(self, finance_service: Any | None, *, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = finance_service
        self._language = "zh_CN"
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Global validated finance items", self))
        self.item_list = QListWidget(self)
        self.item_list.itemChanged.connect(self._item_changed)
        layout.addWidget(self.item_list, 1)
        for title, callback in (
            ("Move Up", lambda: self.move_selected(-1)),
            ("Move Down", lambda: self.move_selected(1)),
        ):
            button = QPushButton(title, self)
            button.clicked.connect(callback)
            layout.addWidget(button)
        self.status_label = QLabel(self)
        layout.addWidget(self.status_label)
        self.refresh()

    def refresh(self) -> None:
        if self._service is None:
            self.item_list.clear()
            self.status_label.setText(
                translate_text("Finance service unavailable", self._language)
            )
            return
        selected_key = self._selected_key()
        with QSignalBlocker(self.item_list):
            self.item_list.clear()
            for item in self._service.ordered_items():
                row = QListWidgetItem(item.display_name, self.item_list)
                row.setData(Qt.ItemDataRole.UserRole, item.key)
                row.setFlags(row.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                row.setCheckState(
                    Qt.CheckState.Checked
                    if self._service.is_enabled(item.key)
                    else Qt.CheckState.Unchecked
                )
                if item.key == selected_key:
                    self.item_list.setCurrentItem(row)
        enabled = len(self._service.enabled_items())
        self.status_label.setText(
            (
                f"已启用 {enabled} 项；顺序为全局设置"
                if self._language == "zh_CN"
                else f"{enabled} enabled; order is global"
            )
        )

    def set_language(self, language: str) -> None:
        if language not in SUPPORTED_LANGUAGES:
            return
        self._language = language
        self.refresh()

    def set_item_enabled(self, item_key: str, enabled: bool) -> bool:
        if self._service is None:
            return False
        try:
            self._service.set_enabled(item_key, enabled)
        except (LookupError, TypeError, ValueError) as error:
            self.status_label.setText(str(error))
            return False
        self.refresh()
        return True

    def move_selected(self, delta: int) -> bool:
        if self._service is None or self.item_list.currentRow() < 0:
            return False
        row = self.item_list.currentRow()
        target = row + delta
        if target < 0 or target >= self.item_list.count():
            return False
        keys = [
            self.item_list.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.item_list.count())
        ]
        keys[row], keys[target] = keys[target], keys[row]
        try:
            self._service.reorder(keys)
        except (LookupError, TypeError, ValueError) as error:
            self.status_label.setText(str(error))
            return False
        self.refresh()
        self.item_list.setCurrentRow(target)
        return True

    def _item_changed(self, item: QListWidgetItem) -> None:
        key = item.data(Qt.ItemDataRole.UserRole)
        if key is not None:
            self.set_item_enabled(str(key), item.checkState() is Qt.CheckState.Checked)

    def _selected_key(self) -> str | None:
        item = self.item_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return None if value is None else str(value)
