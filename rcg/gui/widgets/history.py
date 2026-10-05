"""Session history of added subcatchments, with undo for the most recent one."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from rcg.gui.categories import catchment_type_label
from rcg.gui.widgets._util import ElidedLabel, divider, hbox, label, set_prop

if TYPE_CHECKING:
    from rcg.catchment import ApplyResult, SubcatchmentParameters

__all__ = ["HistoryEntry", "HistoryPanel"]

_MIN_LIST_HEIGHT = 48


@dataclass
class HistoryEntry:
    """One successful *Add* in this session."""

    subcatchment_ids: tuple[str, ...]
    area_ha: float
    catchment_type: str
    output_path: Path
    backup_path: Path | None
    undone: bool = False
    written_sha256: str | None = None  # file as RCG wrote it; undo refuses once it changed

    @classmethod
    def from_apply(cls, result: ApplyResult, params: SubcatchmentParameters | None) -> HistoryEntry:
        """The entry for a successful apply of *params* (``None`` if they are not known)."""
        return cls(
            subcatchment_ids=tuple(result.subcatchment_ids),
            area_ha=params.area_ha if params is not None else float("nan"),
            catchment_type=params.catchment_type if params is not None else "",
            output_path=Path(result.output_path),
            backup_path=Path(result.backup_path) if result.backup_path is not None else None,
            written_sha256=result.written_sha256,
        )

    @property
    def title(self) -> str:
        return ", ".join(self.subcatchment_ids)


class _HistoryRow(QWidget):
    def __init__(self, entry: HistoryEntry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.entry = entry

        self.title = label(entry.title, "historyTitle", self)
        details = f"{entry.area_ha:.2f} ha  ·  {catchment_type_label(entry.catchment_type)}"
        # Elides before the buttons are pushed out of the (narrow) list.
        self.details = ElidedLabel(details, "caption", self, mode=Qt.TextElideMode.ElideRight)
        self.details.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.state = label("Undone", "pill", self)
        self.state.setVisible(entry.undone)

        self.file = ElidedLabel(entry.output_path.name, "caption", self)
        self.file.setToolTip(str(entry.output_path))
        self.file.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        if entry.backup_path is not None:
            self.backup = ElidedLabel(f"Backup: {entry.backup_path.name}", "caption", self)
            self.backup.setToolTip(str(entry.backup_path))
        else:
            self.backup = ElidedLabel("No backup (written to a new file)", "caption", self)

        self.undo_button = QPushButton("Undo", self)
        self.undo_button.setProperty("flat", True)
        self.undo_button.setToolTip("Restore the model from the backup taken before this subcatchment was added")
        self.undo_button.setAccessibleName(f"Undo adding {entry.title}")
        self.undo_button.hide()
        self.folder_button = QPushButton("Show in folder", self)
        self.folder_button.setProperty("flat", True)
        self.folder_button.setAccessibleName(f"Show {entry.output_path.name} in folder")

        top = hbox(self.title, self.details, self.state, 1, self.undo_button, self.folder_button, spacing=8)
        bottom = hbox(self.file, (self.backup, 1), spacing=12)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)
        layout.addLayout(top)
        layout.addLayout(bottom)

    def refresh(self, *, can_undo: bool) -> None:
        self.state.setVisible(self.entry.undone)
        set_prop(self.title, "undone", self.entry.undone)
        self.undo_button.setVisible(can_undo)


class HistoryPanel(QFrame):
    """Card listing the subcatchments added in this session, newest first."""

    undoRequested = Signal(object)  # HistoryEntry
    showInFolderRequested = Signal(object)  # Path

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("card", True)
        self.setObjectName("historyPanel")
        self.setAccessibleName("History")
        self._rows: list[_HistoryRow] = []

        title = label("History", "sectionTitle", self)
        self.count = label("", "caption", self)
        header = hbox(title, 1, self.count)

        self.placeholder = label(
            "Subcatchments you add appear here. The latest one can be undone from its backup.",
            "placeholder",
            self,
            wrap=True,
        )
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        # Placeholder and list share one minimum height (about one row), so the first
        # entry does not change the window's minimum size.
        self.placeholder.setMinimumHeight(_MIN_LIST_HEIGHT)

        self._content = QWidget()
        self._content.setObjectName("historyContent")
        self._list = QVBoxLayout(self._content)
        self._list.setContentsMargins(0, 0, 4, 0)
        self._list.setSpacing(0)
        self._list.addStretch(1)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidget(self._content)
        self.scroll_area.viewport().setAutoFillBackground(False)
        self._content.setAutoFillBackground(False)
        self.scroll_area.setMinimumHeight(_MIN_LIST_HEIGHT)
        self.scroll_area.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 14, 12)
        layout.setSpacing(8)
        layout.addLayout(header)
        layout.addWidget(self.placeholder, 1)
        layout.addWidget(self.scroll_area, 1)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    # -- public API ------------------------------------------------------------------
    @property
    def entries(self) -> list[HistoryEntry]:
        """Entries, newest first."""
        return [row.entry for row in self._rows]

    def add_entry(self, entry: HistoryEntry) -> None:
        row = _HistoryRow(entry, self._content)
        row.undo_button.clicked.connect(lambda: self.undoRequested.emit(row.entry))
        row.folder_button.clicked.connect(lambda: self.showInFolderRequested.emit(row.entry.output_path))
        if self._rows:
            self._list.insertWidget(0, divider(self._content))
        self._list.insertWidget(0, row)
        self._rows.insert(0, row)
        self.placeholder.hide()
        self.scroll_area.show()
        self.scroll_area.verticalScrollBar().setValue(0)
        self.refresh()

    def undo_candidate(self) -> HistoryEntry | None:
        """The newest entry that has not been undone, if it can be undone (has a backup)."""
        for row in self._rows:
            if not row.entry.undone:
                return row.entry if row.entry.backup_path is not None else None
        return None

    def refresh(self) -> None:
        candidate = self.undo_candidate()
        for row in self._rows:
            row.refresh(can_undo=row.entry is candidate)
        active = sum(1 for row in self._rows if not row.entry.undone)
        self.count.setText(f"{active} added this session" if self._rows else "")

    def undo_button_for(self, entry: HistoryEntry) -> QPushButton | None:
        for row in self._rows:
            if row.entry is entry:
                return row.undo_button
        return None
