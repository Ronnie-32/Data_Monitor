from __future__ import annotations

from pathlib import Path

from app import (
    adjusted_drag_geometry,
    fitted_content_rect,
    image_path_from_config,
    normalize_geometry,
    window_flags_for_mode,
)
from PySide6.QtCore import Qt


def test_normalize_geometry_keeps_valid_saved_geometry() -> None:
    assert normalize_geometry(
        {"x": 120, "y": 80, "width": 900, "height": 560},
        (0, 0, 1920, 1080),
    ) == (120, 80, 900, 560)


def test_normalize_geometry_recovers_an_offscreen_window() -> None:
    assert normalize_geometry(
        {"x": 4000, "y": 3000, "width": 900, "height": 560},
        (0, 0, 1920, 1080),
    ) == (510, 260, 900, 560)


def test_normalize_geometry_limits_tiny_and_oversized_values() -> None:
    assert normalize_geometry(
        {"x": -100, "y": -100, "width": 10, "height": 5000},
        (0, 0, 1920, 1080),
    ) == (0, 0, 240, 1080)


def test_adjusted_drag_geometry_moves_the_whole_window() -> None:
    assert adjusted_drag_geometry((100, 80, 900, 560), (35, -20), frozenset()) == (
        135,
        60,
        900,
        560,
    )


def test_adjusted_drag_geometry_resizes_from_edges_and_respects_minimum() -> None:
    assert adjusted_drag_geometry(
        (100, 80, 900, 560), (50, 30), frozenset({"left", "top"})
    ) == (150, 110, 850, 530)
    assert adjusted_drag_geometry(
        (100, 80, 300, 200), (-500, -500), frozenset({"right", "bottom"})
    ) == (100, 80, 240, 150)


def test_edit_mode_uses_a_normal_windows_frame() -> None:
    edit_flags = window_flags_for_mode(True)
    assert edit_flags & Qt.WindowType.Window
    assert edit_flags & Qt.WindowType.WindowTitleHint
    assert not edit_flags & Qt.WindowType.FramelessWindowHint
    assert not edit_flags & Qt.WindowType.WindowTransparentForInput


def test_locked_mode_is_frameless_and_input_transparent() -> None:
    locked_flags = window_flags_for_mode(False)
    assert locked_flags & Qt.WindowType.FramelessWindowHint
    assert locked_flags & Qt.WindowType.WindowTransparentForInput


def test_fitted_content_rect_preserves_vector_aspect_ratio() -> None:
    assert fitted_content_rect(900, 560, 1176, 1023) == (128, 0, 644, 560)
    assert fitted_content_rect(1600, 1200, 1176, 1023) == (110, 0, 1379, 1200)


def test_missing_image_configuration_requires_user_selection() -> None:
    assert image_path_from_config({}) is None
    assert image_path_from_config({"image": ""}) is None


def test_user_image_path_can_be_relative_or_absolute() -> None:
    assert image_path_from_config({"image": "my-schedule.svg"}) == (
        Path(__file__).resolve().parent / "my-schedule.svg"
    )
    selected = Path("C:/Users/example/Pictures/schedule.png")
    assert image_path_from_config({"image": str(selected)}) == selected
