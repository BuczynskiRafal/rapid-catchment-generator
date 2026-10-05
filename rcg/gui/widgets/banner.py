"""Inline, non-modal message banner (errors, confirmations)."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QSize, Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QToolButton, QWidget

from rcg.gui.widgets._util import WrapLabel, set_prop

__all__ = ["MessageBanner"]

_MARKS = {"error": "!", "success": "✓", "info": "i"}


class MessageBanner(QFrame):
    """A dismissible strip shown above the content; hidden while empty.

    The banner spans its parent's layout, so its height is computed for that width
    (height-for-width): a long message takes exactly the lines it needs and the window
    grows by that much instead of squeezing the content underneath.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("messageBanner")
        self.setProperty("banner", "info")
        self.setAccessibleName("Message")

        self._mark = QLabel(self)
        self._mark.setProperty("role", "bannerMark")
        self._mark.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self._mark.setFixedWidth(14)

        # Height-for-width aware: the window reserves exactly the lines the text needs,
        # so a long message never squeezes the cards below it.
        self._text = WrapLabel("", None, self)
        self._text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._text.setTextFormat(Qt.TextFormat.PlainText)

        self._close = QToolButton(self)
        self._close.setText("×")
        self._close.setToolTip("Dismiss")
        self._close.setAccessibleName("Dismiss message")
        self._close.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close.clicked.connect(self.dismiss)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(10)
        layout.addWidget(self._mark)
        layout.addWidget(self._text, 1)
        layout.addWidget(self._close, 0, Qt.AlignmentFlag.AlignTop)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        if parent is not None:
            parent.installEventFilter(self)  # re-wrap when the parent's width changes
        self.hide()

    # -- geometry --------------------------------------------------------------------
    def _intended_width(self) -> int:
        """The width the parent's layout gives the banner (it spans the whole layout)."""
        parent = self.parentWidget()
        layout = parent.layout() if parent is not None else None
        if parent is None or layout is None:
            return self.width()
        margins = layout.contentsMargins()
        return max(0, parent.contentsRect().width() - margins.left() - margins.right())

    def _height_for(self, width: int) -> int:
        layout = self.layout()
        if layout is None or width <= 0:
            return super().sizeHint().height()
        return layout.totalHeightForWidth(width) if layout.hasHeightForWidth() else layout.totalSizeHint().height()

    def sizeHint(self) -> QSize:
        width = self._intended_width()
        return QSize(width, self._height_for(width))

    def minimumSizeHint(self) -> QSize:
        hint = super().minimumSizeHint()
        return QSize(hint.width(), self._height_for(self._intended_width()))

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.parentWidget() and event.type() == QEvent.Type.Resize and self.isVisible():
            self.updateGeometry()
        return False

    # -- public API ------------------------------------------------------------------
    def show_message(self, kind: str, text: str, *, timeout_ms: int = 0) -> None:
        """Show *text* with style *kind* (``error``, ``success`` or ``info``)."""
        self._timer.stop()
        set_prop(self, "banner", kind)
        # Descendant selectors depend on the banner kind: re-polish the children too.
        for child in (self._mark, self._text, self._close):
            child.style().unpolish(child)
            child.style().polish(child)
        self._mark.setText(_MARKS.get(kind, ""))
        self._text.setText(text)
        self.setAccessibleDescription(text)
        self.show()
        if timeout_ms > 0:
            self._timer.start(timeout_ms)

    def show_error(self, text: str) -> None:
        self.show_message("error", text)

    def dismiss(self) -> None:
        self._timer.stop()
        self.hide()

    @property
    def kind(self) -> str:
        return str(self.property("banner"))

    @property
    def text(self) -> str:
        return self._text.text()
