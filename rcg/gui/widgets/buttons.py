"""Buttons with a focus indicator that never shares a colour with a button state."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QPushButton, QWidget

from rcg.gui.theme import current_tokens

__all__ = ["PrimaryButton"]

_RING_INSET = 3.0
_RING_WIDTH = 1.5
_RING_RADIUS = 4.0


class PrimaryButton(QPushButton):
    """The filled accent button.

    Hover, pressed and disabled all change the fill, so a focus border in the accent
    colour would be invisible. Keyboard focus is instead shown as an inner ring in the
    on-accent colour (the text colour), inset from the edge: accent outside, light
    ring, accent inside, in light and dark mode alike.

    The button takes focus from the keyboard only (like a macOS push button), so a
    mouse click never leaves a ring behind.
    """

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setProperty("primary", True)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setAutoDefault(False)

    def focus_ring_visible(self) -> bool:
        return self.hasFocus() and self.isEnabled()

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        if not self.focus_ring_visible():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(current_tokens().on_accent), _RING_WIDTH)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        inset = _RING_INSET + _RING_WIDTH / 2
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(inset, inset, -inset, -inset), _RING_RADIUS, _RING_RADIUS)
        painter.end()
