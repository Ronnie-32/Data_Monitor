"""Operating modes shared by the application shell and later UI tasks."""

from enum import Enum


class AppMode(Enum):
    LOCKED = "locked"
    INTERACTION = "interaction"
    LAYOUT_EDIT = "layout_edit"
