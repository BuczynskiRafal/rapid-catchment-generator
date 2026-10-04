"""Small helpers shared by the widgets."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from PySide6.QtCore import QEvent, QRect, QSize, Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QBoxLayout, QFrame, QHBoxLayout, QLabel, QLayout, QSizePolicy, QVBoxLayout, QWidget


def set_prop(widget: QWidget, name: str, value: Any) -> None:
    """Set a dynamic property used by the style sheet and re-polish if it changed."""
    if widget.property(name) == value:
        return
    widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def label(text: str = "", role: str | None = None, parent: QWidget | None = None, *, wrap: bool = False) -> QLabel:
    """Create a label with a style-sheet *role*; ``wrap=True`` returns a :class:`WrapLabel`."""
    if wrap:
        return WrapLabel(text, role, parent)
    lbl = QLabel(text, parent)
    if role:
        lbl.setProperty("role", role)
    return lbl


def card(parent: QWidget | None = None, name: str | None = None) -> QFrame:
    """Create a card container (soft border, rounded, palette-derived background)."""
    frame = QFrame(parent)
    frame.setProperty("card", True)
    if name:
        frame.setObjectName(name)
    return frame


def divider(parent: QWidget | None = None) -> QFrame:
    """Create a 1 px horizontal divider."""
    line = QFrame(parent)
    line.setProperty("divider", True)
    line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return line


LayoutItem = QWidget | QLayout | int | tuple[QWidget | QLayout, int] | tuple[QWidget, int, Qt.AlignmentFlag]
"""An entry for :func:`hbox` / :func:`vbox`: a widget, a layout, a stretch factor (``int``),
``(widget_or_layout, stretch)`` or ``(widget, stretch, alignment)``."""


def _fill(box: QBoxLayout, items: Iterable[LayoutItem], spacing: int | None) -> None:
    box.setContentsMargins(0, 0, 0, 0)
    if spacing is not None:
        box.setSpacing(spacing)
    for item in items:
        if isinstance(item, int):
            box.addStretch(item)
        elif isinstance(item, QLayout):
            box.addLayout(item)
        elif isinstance(item, QWidget):
            box.addWidget(item)
        elif isinstance(item[0], QLayout):
            box.addLayout(item[0], item[1])
        else:
            box.addWidget(*item)  # type: ignore[arg-type]


def hbox(*items: LayoutItem, spacing: int | None = None, parent: QWidget | None = None) -> QHBoxLayout:
    """Return a margin-less horizontal layout holding *items* (see :data:`LayoutItem`).

    ``spacing=None`` keeps the style's default spacing; *parent* installs the layout on it.
    """
    box = QHBoxLayout(parent) if parent is not None else QHBoxLayout()
    _fill(box, items, spacing)
    return box


def vbox(*items: LayoutItem, spacing: int | None = None, parent: QWidget | None = None) -> QVBoxLayout:
    """Return a margin-less vertical layout holding *items* (see :data:`LayoutItem`)."""
    box = QVBoxLayout(parent) if parent is not None else QVBoxLayout()
    _fill(box, items, spacing)
    return box


def set_tab_order(widgets: Iterable[QWidget]) -> None:
    """Make Tab move through *widgets* in the given order."""
    chain = list(widgets)
    for first, second in zip(chain, chain[1:]):
        QWidget.setTabOrder(first, second)


class WrapLabel(QLabel):
    """Word-wrapped label whose height always matches its text at its current width.

    ``QLabel`` with word wrap reports a size hint for a heuristic width, which inside
    nested layouts yields clipped or overly tall rows. This label reports the height
    for the width it actually has. ``reserve_lines`` keeps a minimum number of lines
    so alternating short and long texts do not make the layout jump.
    """

    def __init__(self, text: str = "", role: str | None = None, parent: QWidget | None = None, *, reserve_lines: int = 0):
        super().__init__(text, parent)
        if role:
            self.setProperty("role", role)
        self.setWordWrap(True)
        self._reserve_lines = reserve_lines
        self._last_width = -1
        policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def _height_for(self, width: int) -> int:
        self.ensurePolished()  # the style sheet may change the font size
        reserved = 0
        if self._reserve_lines:
            # Measured like QLabel measures wrapped text, so a text that does take the
            # reserved number of lines is exactly as tall as the reservation.
            lines = "\n".join("X" * self._reserve_lines)
            flags = int(Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap)
            margins = self.contentsMargins()
            reserved = (
                self.fontMetrics().boundingRect(QRect(0, 0, 10_000, 10_000), flags, lines).height()
                + 2 * self.margin()
                + margins.top()
                + margins.bottom()
            )
        needed = self.heightForWidth(width) if width > 0 else super().sizeHint().height()
        return max(needed, reserved)

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        width = self.width() if self.width() > 0 else base.width()
        return QSize(base.width(), self._height_for(width))

    def minimumSizeHint(self) -> QSize:
        base = super().minimumSizeHint()
        width = self.width() if self.width() > 0 else base.width()
        return QSize(min(base.width(), 80), self._height_for(width))

    def setText(self, text: str) -> None:
        super().setText(text)
        self.updateGeometry()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if event.size().width() != self._last_width:
            self._last_width = event.size().width()
            self.updateGeometry()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self.updateGeometry()


class ElidedLabel(QLabel):
    """Single-line label that elides (by default in the middle) instead of growing.

    The full text is available as the tooltip and through :meth:`full_text`.
    """

    def __init__(
        self,
        text: str = "",
        role: str | None = None,
        parent: QWidget | None = None,
        *,
        mode: Qt.TextElideMode = Qt.TextElideMode.ElideMiddle,
    ) -> None:
        super().__init__(parent)
        if role:
            self.setProperty("role", role)
        self._full = ""
        self._mode = mode
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setText(text)

    def full_text(self) -> str:
        return self._full

    def setText(self, text: str) -> None:
        self._full = text
        self.setToolTip(text)
        self.setAccessibleDescription(text)  # screen readers get the full, un-elided text
        self._refresh()

    def _line_height(self, base: int) -> int:
        """One line's height whether or not there is text (an empty QLabel is a pixel shorter)."""
        margins = self.contentsMargins()
        line = self.fontMetrics().boundingRect(QRect(0, 0, 10_000, 1_000), int(Qt.AlignmentFlag.AlignLeft), "X").height()
        return max(base, line + 2 * self.margin() + margins.top() + margins.bottom())

    def minimumSizeHint(self) -> QSize:
        return QSize(24, self._line_height(super().minimumSizeHint().height()))

    def sizeHint(self) -> QSize:
        return QSize(self.fontMetrics().horizontalAdvance(self._full) + 4, self._line_height(super().sizeHint().height()))

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._refresh()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self._refresh()

    def _refresh(self) -> None:
        width = max(0, self.width() - 2)
        super().setText(self.fontMetrics().elidedText(self._full, self._mode, width) if width else self._full)


class ReservedLabel(QLabel):
    """Single-line label whose width covers a fixed set of *samples*, whatever it shows.

    The hint is computed on demand from the label's current font (so it is right once
    the style sheet has been applied, and follows theme or font changes), which keeps
    the layout, and with it the window's minimum size, unchanged when the text changes:
    the placeholder ``—`` reserves as much room as the widest value it can be replaced by.
    A text wider than every sample still gets its room rather than being clipped.
    """

    def __init__(
        self, text: str = "", role: str | None = None, parent: QWidget | None = None, *, samples: Iterable[str] = ()
    ) -> None:
        super().__init__(text, parent)
        if role:
            self.setProperty("role", role)
        self._samples = tuple(samples)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

    def set_samples(self, samples: Iterable[str]) -> None:
        self._samples = tuple(samples)
        self.updateGeometry()

    def _reserved_width(self) -> int:
        self.ensurePolished()
        metrics = self.fontMetrics()
        widest = max((metrics.horizontalAdvance(text) for text in (*self._samples, self.text())), default=0)
        margins = self.contentsMargins()
        return widest + 2 * self.margin() + margins.left() + margins.right() + 2

    def sizeHint(self) -> QSize:
        return QSize(self._reserved_width(), super().sizeHint().height())

    def minimumSizeHint(self) -> QSize:
        return QSize(self._reserved_width(), super().minimumSizeHint().height())

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self.updateGeometry()
