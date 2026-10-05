"""Containers that keep the main window's minimum size right.

* :class:`WindowCentral`: the central widget; never smaller than the design minimum.
* :class:`VerticalScrollArea`: holds the cards; as tall as its content, scrolling only
  when that would not fit on the screen.
* :func:`invalidate_layouts`: drop cached layout sizes at once instead of over two
  event-loop passes.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QSize
from PySide6.QtWidgets import QLayout, QMainWindow, QMenuBar, QScrollArea, QSizePolicy, QWidget

__all__ = ["VerticalScrollArea", "WindowCentral", "invalidate_layouts"]


class WindowCentral(QWidget):
    """Central widget that keeps the window at least at the design minimum (860 x 560).

    The window's minimum size is otherwise left to the layout, so content that needs more
    room (a long error banner, large system fonts) grows the window instead of overlapping.
    """

    WINDOW_MINIMUM = QSize(860, 560)

    def minimumSizeHint(self) -> QSize:
        minimum = QSize(self.WINDOW_MINIMUM)
        window = self.window()
        bar = window.menuWidget() if isinstance(window, QMainWindow) else None
        if isinstance(bar, QMenuBar) and not bar.isNativeMenuBar():
            minimum.setHeight(minimum.height() - bar.sizeHint().height())  # the bar is part of the window
        return super().minimumSizeHint().expandedTo(minimum)


class VerticalScrollArea(QScrollArea):
    """Scrolls vertically only, never narrower than its content.

    Its minimum height is the content's, so the cards are fully visible at the window's
    minimum size and the scroll bar never appears. Only when that would not fit on the
    screen (very large fonts, small displays) does it fall back to scrolling, and only
    then is room for the scroll bar reserved. It asks for no more than its content's
    height either, so any extra window height goes to the history below it.
    """

    SCREEN_SHARE = 0.6  # at most this share of the screen height is claimed as minimum

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def setWidget(self, widget: QWidget) -> None:
        super().setWidget(widget)
        widget.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # QScrollArea does not pass size changes of its content on to its own parent
        # layout, which would keep using a stale (e.g. pre-style-sheet) minimum width.
        if watched is self.widget() and event.type() == QEvent.Type.LayoutRequest:
            self.updateGeometry()
        return super().eventFilter(watched, event)

    def minimumSizeHint(self) -> QSize:
        hint = super().minimumSizeHint()
        content = self.widget()
        if content is None:
            return hint
        frame = 2 * self.frameWidth()
        content_hint = content.minimumSizeHint()
        width = content_hint.width() + frame
        height = content_hint.height() + frame
        content_layout = content.layout()
        if content_layout is not None and content_layout.hasHeightForWidth():
            # QScrollArea uses heightForWidth when sizing its resizable content.
            # The layout's minimumHeightForWidth can be smaller (e.g. baseline
            # aligned labels), leaving a few pixels to scroll even on a large screen.
            target_width = max(content_hint.width(), self.width() - frame)
            hfw = content_layout.heightForWidth(target_width)
            if hfw > 0:
                height = max(height, hfw + frame)
        screen = self.screen()
        if screen is not None:
            cap = int(screen.availableGeometry().height() * self.SCREEN_SHARE)
            if height > cap:
                height = cap
                width += self.verticalScrollBar().sizeHint().width()
        return QSize(max(hint.width(), width), max(hint.height(), height))

    def sizeHint(self) -> QSize:
        return self.minimumSizeHint()


def invalidate_layouts(layout: QLayout) -> None:
    """Drop the cached sizes of *layout* and every layout nested in it (innermost first)."""
    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item is None:
            continue
        child = item.layout()
        if child is not None:
            invalidate_layouts(child)
        widget = item.widget()
        if widget is not None:
            widget_layout = widget.layout()
            if widget_layout is not None:
                invalidate_layouts(widget_layout)
            for sub in widget.findChildren(QWidget):
                sub_layout = sub.layout()
                if sub_layout is not None:
                    sub_layout.invalidate()
    layout.invalidate()
