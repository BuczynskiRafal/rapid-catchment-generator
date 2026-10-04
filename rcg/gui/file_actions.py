"""File operations triggered from the history list (show in folder).

Undo is :func:`rcg.restore`; it lives in the library so the CLI and the API share it.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

__all__ = ["show_in_folder"]


def show_in_folder(path: Path) -> bool:
    """Open the folder containing *path* in the system file manager."""
    folder = Path(path)
    if not folder.is_dir():
        folder = folder.parent
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
