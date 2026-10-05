"""Help window rendering ``resources/help.md``."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTextBrowser, QVBoxLayout, QWidget

from rcg.gui.resources import read_text
from rcg.logging_config import get_logger

__all__ = ["HelpDialog", "load_help_markdown"]

logger = get_logger("gui")  # one logger for the whole GUI (rcg.gui)

_FALLBACK = (
    "# Rapid Catchment Generator\n\nThe help file could not be found. See "
    "<https://github.com/BuczynskiRafal/rapid-catchment-generator> for documentation."
)


def load_help_markdown() -> str:
    try:
        return read_text("help.md")
    except OSError:
        logger.warning("help.md resource is missing", exc_info=True)
        return _FALLBACK


class HelpDialog(QDialog):
    """Non-modal, resizable help window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rapid Catchment Generator Help")
        self.setModal(False)
        self.setMinimumSize(560, 420)
        self.resize(780, 680)

        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(True)
        self.browser.setAccessibleName("Help text")
        self.browser.document().setDocumentMargin(12)
        self.browser.document().setDefaultStyleSheet("table { border-collapse: collapse; } th, td { padding: 4px 8px; }")
        self.browser.setMarkdown(load_help_markdown())

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setAutoDefault(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(12)
        layout.addWidget(self.browser, 1)
        layout.addWidget(buttons, 0, Qt.AlignmentFlag.AlignRight)
