import pytest

from deskboard.app.modes import AppMode


def test_app_mode_exposes_only_the_three_documented_modes():
    assert {mode.value for mode in AppMode} == {"locked", "interaction", "layout_edit"}
    assert AppMode("locked") is AppMode.LOCKED
    assert AppMode("interaction") is AppMode.INTERACTION
    assert AppMode("layout_edit") is AppMode.LAYOUT_EDIT


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError):
        AppMode("editing")
