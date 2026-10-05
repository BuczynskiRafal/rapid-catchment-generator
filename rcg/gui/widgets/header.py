"""The window header: application icon, title and subtitle, and the help button."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from rcg.gui.resources import resource_path
from rcg.gui.widgets._util import ElidedLabel, LayoutItem, hbox, label, vbox

__all__ = ["HEADER_ICON", "build_header"]

HEADER_ICON = 40


def build_header(parent: QWidget, title: str, subtitle: str) -> tuple[QHBoxLayout, QToolButton]:
    """Return the header row and its help button (the caller connects it).

    The icon is left out when the resource is missing.
    """
    title_label = label(title, "title", parent)
    title_label.setAccessibleName(title)
    subtitle_label = ElidedLabel(subtitle, "subtitle", parent)
    subtitle_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    help_button = QToolButton(parent)
    help_button.setText("?")
    help_button.setProperty("role", "help")
    help_button.setToolTip("Help (F1)")
    help_button.setAccessibleName("Help")
    help_button.setCursor(Qt.CursorShape.PointingHandCursor)

    centred = Qt.AlignmentFlag.AlignVCenter
    icon = _app_icon(parent, title)
    leading: tuple[LayoutItem, ...] = ((icon, 0, centred),) if icon is not None else ()
    titles = vbox(title_label, subtitle_label, spacing=0)
    return hbox(*leading, (titles, 1), (help_button, 0, centred), spacing=12), help_button


def _app_icon(parent: QWidget, accessible_name: str) -> QLabel | None:
    """The application icon, sharp on high-DPI screens; ``None`` if it is missing."""
    path = resource_path("icon.png")
    if path is None:
        return None
    size = QSize(HEADER_ICON, HEADER_ICON)
    pixmap = QIcon(str(path)).pixmap(size, parent.devicePixelRatioF())
    if pixmap.isNull():
        return None
    icon = QLabel(parent)
    icon.setObjectName("appIcon")
    icon.setPixmap(pixmap)
    icon.setFixedSize(size)
    icon.setAccessibleName(accessible_name)
    return icon
