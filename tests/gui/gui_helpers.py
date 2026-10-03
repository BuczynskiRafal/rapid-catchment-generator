"""Helpers shared by the GUI test modules."""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

ENGINE_TIMEOUT_MS = 120_000
APPLY_TIMEOUT_MS = 30_000
PREVIEW_TIMEOUT_MS = 10_000

LONG_ERROR = (
    "File does not exist: '/Users/someone/Documents/models/very/long/path/to/the/model/directory/structure/"
    "that/keeps/going/catchment_with_a_long_name.inp'. Details were written to /Users/someone/Library/"
    "Application Support/Rapid Catchment Generator/rcg-gui.log."
)


def subcatchment_ids(path: Path) -> list[str]:
    import swmmio

    return [str(name) for name in swmmio.Model(str(path)).inp.subcatchments.index]


def subcatchment_areas(path: Path) -> dict[str, float]:
    import swmmio

    table = swmmio.Model(str(path)).inp.subcatchments
    return {str(name): float(area) for name, area in table["Area"].items()}


def select(combo, member) -> None:
    index = combo.findData(member)
    assert index >= 0, member
    combo.setCurrentIndex(index)


def add_and_wait(qtbot, window) -> None:
    count = len(window.history.entries)
    qtbot.mouseClick(window.add_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: not window.busy and len(window.history.entries) > count, timeout=APPLY_TIMEOUT_MS)


def save_screenshot(widget, dirs: list[Path], name: str) -> None:
    QApplication.processEvents()
    image = widget.grab()
    assert not image.isNull()
    for directory in dirs:
        assert image.save(str(directory / name))


def make_us_model(source: Path, target: Path, *, flow_units: str = "CFS", infiltration: str = "HORTON") -> Path:
    """Copy *source* with other ``FLOW_UNITS`` and ``INFILTRATION`` options."""
    text = source.read_text()
    text = re.sub(r"^(FLOW_UNITS\s+)\S+", rf"\g<1>{flow_units}", text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^(INFILTRATION\s+)\S+", rf"\g<1>{infiltration}", text, count=1, flags=re.MULTILINE)
    target.write_text(text)
    return target


def dark_palette() -> QPalette:
    palette = QPalette()
    colors = {
        QPalette.ColorRole.Window: "#2b2b2d",
        QPalette.ColorRole.WindowText: "#e6e6e6",
        QPalette.ColorRole.Base: "#1e1e20",
        QPalette.ColorRole.AlternateBase: "#262628",
        QPalette.ColorRole.Text: "#e6e6e6",
        QPalette.ColorRole.Button: "#3a3a3c",
        QPalette.ColorRole.ButtonText: "#e6e6e6",
        QPalette.ColorRole.ToolTipBase: "#2b2b2d",
        QPalette.ColorRole.ToolTipText: "#e6e6e6",
        QPalette.ColorRole.PlaceholderText: "#8a8a8e",
        QPalette.ColorRole.Highlight: "#3a6ea5",
        QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.Light: "#4a4a4c",
        QPalette.ColorRole.Midlight: "#404042",
        QPalette.ColorRole.Mid: "#3a3a3c",
        QPalette.ColorRole.Dark: "#1a1a1a",
        QPalette.ColorRole.Shadow: "#000000",
    }
    for role, color in colors.items():
        palette.setColor(role, QColor(color))
    return palette
