"""File operations triggered from the history list (undo, show in folder)."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

__all__ = ["restore_backup", "show_in_folder"]


def restore_backup(backup_path: Path, target_path: Path) -> None:
    """Copy *backup_path* back over *target_path* atomically; the backup is kept.

    Raises ``FileNotFoundError`` when the backup no longer exists and ``OSError`` for
    any other I/O problem; the target is never left half-written.
    """
    backup_path = Path(backup_path)
    target_path = Path(target_path)
    if not backup_path.is_file():
        raise FileNotFoundError(f"Backup no longer exists: {backup_path}")
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target_path.stem}.", suffix=".restore", dir=target_path.parent)
    os.close(fd)
    try:
        shutil.copy2(backup_path, tmp_name)
        os.replace(tmp_name, target_path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def show_in_folder(path: Path) -> bool:
    """Open the folder containing *path* in the system file manager."""
    folder = Path(path)
    if not folder.is_dir():
        folder = folder.parent
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
