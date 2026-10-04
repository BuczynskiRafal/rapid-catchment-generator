"""Dropping a file anywhere on a window.

:class:`FileDropFilter` is an event filter: installed on a widget, it accepts a local
file dragged onto any part of it that does not take the drop itself, highlights the
drop zone while the file hovers, and hands the dropped path to a callback.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QMimeData, QObject
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QWidget

__all__ = ["FileDropFilter", "dropped_file"]


def dropped_file(mime: QMimeData) -> str | None:
    """The first local file in *mime*, or ``None``."""
    if not mime.hasUrls():
        return None
    for url in mime.urls():
        if url.isLocalFile():
            return url.toLocalFile()
    return None


class FileDropFilter(QObject):
    """Make *target* accept dropped files.

    Parameters
    ----------
    target : QWidget
        The widget (usually a window) that accepts drops; it also owns the filter.
    dropped : callable
        Called with the path of a dropped local file.
    highlight : callable
        Called with ``True`` while a file hovers over *target* and ``False`` once it
        leaves or is dropped.
    """

    def __init__(self, target: QWidget, *, dropped: Callable[[str], None], highlight: Callable[[bool], None]) -> None:
        super().__init__(target)
        self._dropped = dropped
        self._highlight = highlight
        target.setAcceptDrops(True)
        target.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        kind = event.type()
        if kind == QEvent.Type.DragEnter and isinstance(event, QDragEnterEvent):
            if dropped_file(event.mimeData()):
                event.acceptProposedAction()
                self._highlight(True)
            else:
                event.ignore()
            return True
        if kind == QEvent.Type.DragMove and isinstance(event, QDragMoveEvent):
            if dropped_file(event.mimeData()):
                event.acceptProposedAction()
            return True
        if kind == QEvent.Type.DragLeave:
            self._highlight(False)
            return False  # the target still sees it
        if kind == QEvent.Type.Drop and isinstance(event, QDropEvent):
            self._highlight(False)
            filename = dropped_file(event.mimeData())
            if filename:
                event.acceptProposedAction()
                self._dropped(filename)
            return True
        return super().eventFilter(watched, event)
