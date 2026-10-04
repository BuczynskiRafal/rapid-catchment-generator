"""File operations of the window: choosing where a copy goes, and showing a file in its folder.

Undo is :func:`rcg.restore`; it lives in the library so the CLI and the API share it.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox, QWidget

from rcg.gui.widgets.path_field import INP_FILTER

__all__ = [
    "ask_save_path",
    "choose_output_path",
    "confirm_replace",
    "copy_suggestion",
    "normalise_output_path",
    "show_in_folder",
]


def show_in_folder(path: Path) -> bool:
    """Open the folder containing *path* in the system file manager."""
    folder = Path(path)
    if not folder.is_dir():
        folder = folder.parent
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))


def normalise_output_path(path: Path) -> Path:
    """Make sure *path* ends in ``.inp`` by appending it (``model_v1.1`` -> ``model_v1.1.inp``).

    The suffix is appended, never substituted: replacing it would turn a dotted name
    into a different, possibly existing, sibling file.
    """
    return path if path.suffix.lower() == ".inp" else path.with_name(f"{path.name}.inp")


def copy_suggestion(source: Path) -> Path:
    """``<stem>_rcg.inp`` next to the source, numbered if that file already exists."""
    candidate = source.with_name(f"{source.stem}_rcg.inp")
    number = 2
    while candidate.exists() and number < 100:
        candidate = source.with_name(f"{source.stem}_rcg_{number}.inp")
        number += 1
    return candidate


def choose_output_path(source: Path, *, ask: Callable[[Path], str | None], confirm: Callable[[Path], bool]) -> Path | None:
    """Where to save a copy of *source*; ``None`` when cancelled.

    *ask* runs the save dialog for a suggested path. A name it returns without ``.inp``
    gets the suffix appended, and if that file exists (the dialog never saw that name)
    *confirm* is asked before it is replaced.
    """
    chosen = ask(copy_suggestion(source))
    if not chosen:
        return None
    confirmed = Path(chosen)
    path = normalise_output_path(confirmed)
    if path != confirmed and path.exists() and not confirm(path):
        return None
    return path


def ask_save_path(parent: QWidget, suggestion: Path) -> str | None:
    """Run the save dialog starting at *suggestion*; the chosen file, or ``None``."""
    dialog = QFileDialog(parent, "Save model as", str(suggestion.parent), INP_FILTER)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    dialog.setFileMode(QFileDialog.FileMode.AnyFile)
    dialog.setDefaultSuffix("inp")
    dialog.selectFile(str(suggestion))
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    files = dialog.selectedFiles()
    return files[0] if files else None


def confirm_replace(parent: QWidget, path: Path) -> bool:
    """Ask before overwriting *path*, a file the save dialog did not confirm."""
    answer = QMessageBox.question(
        parent,
        "Replace file?",
        f"{path.name} already exists in {path.parent}.\nDo you want to replace it?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return answer == QMessageBox.StandardButton.Yes
