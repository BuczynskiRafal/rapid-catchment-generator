"""SWMM model picker: path field, Browse button and an inline two-line model summary."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget

from rcg.exceptions import RCGError
from rcg.gui.categories import infiltration_method_label
from rcg.gui.widgets._util import ElidedLabel, set_prop
from rcg.validation import validate_inp_path

if TYPE_CHECKING:
    from rcg.catchment import ModelInfo

__all__ = [
    "INP_FILTER",
    "ModelPathField",
    "describe_model",
    "describe_model_detail",
    "describe_model_detail_tooltip",
    "format_size",
    "inspect_model_path",
]

INP_FILTER = "SWMM model (*.inp);;All files (*)"
US_UNITS_NOTE = "US units: converted to acres, ft and in on write"
US_UNITS_TOOLTIP = (
    "The model uses US customary units. RCG computes in hectares, metres and millimetres and "
    "converts area, width and depression storage to acres, feet and inches when it writes."
)
_SEP = " · "


def format_size(size_bytes: int) -> str:
    """Human file size (``9971 -> "9.7 KB"``)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    kb = size_bytes / 1024
    if kb < 10:
        return f"{kb:.1f} KB"
    if kb < 1024:
        return f"{kb:.0f} KB"
    return f"{kb / 1024:.1f} MB"


def describe_model(info: ModelInfo) -> str:
    """First summary line: ``"15 subcatchments · CMS · Modified Green-Ampt · 9.7 KB"``."""
    count = info.subcatchment_count
    parts = (
        f"{count} subcatchment{'' if count == 1 else 's'}",
        info.flow_units,
        infiltration_method_label(info.infiltration_method),
        format_size(info.size_bytes),
    )
    return _SEP.join(parts)


def describe_model_detail(info: ModelInfo) -> str:
    """Second summary line: the US-units note, or what new subcatchments connect to."""
    if not info.is_metric:
        return US_UNITS_NOTE
    return f"Rain gage {info.raingage or 'RG1 (new)'}{_SEP}outlet {info.outlet or 'none'}"


def describe_model_detail_tooltip(info: ModelInfo) -> str:
    """The full explanation behind :func:`describe_model_detail`."""
    gage = f"rain gage {info.raingage}" if info.raingage else "a new rain gage RG1"
    outlet = f"drain to {info.outlet}" if info.outlet else "drain to themselves (the model has no outfall or junction)"
    connection = f"New subcatchments use {gage} and {outlet}."
    return connection if info.is_metric else f"{US_UNITS_TOOLTIP}\n{connection}"


def inspect_model_path(text: str) -> tuple[ModelInfo | None, str]:
    """Return ``(info, "")`` for a usable SWMM model or ``(None, reason)`` otherwise."""
    text = text.strip()
    if not text:
        return None, ""
    from rcg import service  # light: does not load the fuzzy engine

    try:
        path = validate_inp_path(text)
        return service.inspect(path), ""
    except RCGError as exc:
        return None, str(exc)


class ModelPathField(QWidget):
    """Line edit + Browse button; drag & drop is handled by the window and routed here.

    The text is validated and the model read with :func:`rcg.service.inspect` (a fast
    text scan, cached per file state). ``modelChanged`` fires with the
    :class:`~rcg.catchment.ModelInfo`, or ``None`` while the text is empty or not a
    usable model; the reason is shown in the inline captions.
    """

    modelChanged = Signal(object)  # ModelInfo | None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._info: ModelInfo | None = None
        self._cache: tuple[tuple[str, int, int], ModelInfo] | None = None
        self._start_dir = ""
        self._hint = "Browse, or drop an .inp file onto the window."

        self.edit = QLineEdit(self)
        self.edit.setPlaceholderText("No model selected")
        self.edit.setMinimumWidth(90)
        self.edit.setClearButtonEnabled(True)
        self.edit.setAcceptDrops(False)  # drops bubble up to the window, which accepts files
        self.edit.setAccessibleName("SWMM model file")
        self.edit.textChanged.connect(self._revalidate)

        self.browse_button = QPushButton("Browse…", self)
        self.browse_button.setAccessibleName("Browse for SWMM model")
        self.browse_button.clicked.connect(self.browse)

        # Not part of this widget's layout: the window places them under the field row.
        # Both lines always exist, so choosing a model never changes the card's height.
        self.message = ElidedLabel(self._hint, "caption", parent, mode=Qt.TextElideMode.ElideRight)
        self.message.setAccessibleName("Model status")
        self.detail = ElidedLabel("", "caption", parent, mode=Qt.TextElideMode.ElideRight)
        self.detail.setAccessibleName("Model details")

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self.edit, 1)
        row.addWidget(self.browse_button)

    # -- public API ------------------------------------------------------------------
    def path(self) -> Path | None:
        """The model path (resolved), or ``None``."""
        return self._info.path if self._info is not None else None

    def model_info(self) -> ModelInfo | None:
        return self._info

    def text(self) -> str:
        return self.edit.text()

    def set_path(self, path: str | Path) -> None:
        self.edit.setText(str(path))
        self.edit.setCursorPosition(len(self.edit.text()))

    def set_start_directory(self, directory: str) -> None:
        self._start_dir = directory

    def set_drop_highlight(self, active: bool) -> None:
        set_prop(self.edit, "dropTarget", active)

    def browse(self) -> None:
        current = self.path()
        start = str(current.parent) if current else self._start_dir
        filename, _ = QFileDialog.getOpenFileName(self, "Open SWMM model", start, INP_FILTER)
        if filename:
            self.set_path(filename)

    def revalidate(self) -> None:
        """Re-read the model (e.g. after RCG or another program changed it)."""
        self._revalidate(self.edit.text())

    # -- internals -------------------------------------------------------------------
    def _inspect(self, text: str) -> tuple[ModelInfo | None, str]:
        """:func:`inspect_model_path`, skipped while the file's size and mtime are unchanged."""
        stripped = text.strip()
        try:
            stat = Path(stripped).expanduser().stat() if stripped else None
        except OSError:
            stat = None
        key = (stripped, stat.st_mtime_ns, stat.st_size) if stat is not None else None
        if key is not None and self._cache is not None and self._cache[0] == key:
            return self._cache[1], ""
        info, reason = inspect_model_path(text)
        self._cache = (key, info) if key is not None and info is not None else None
        return info, reason

    def _revalidate(self, text: str) -> None:
        info, reason = self._inspect(text)
        if info is not None:
            summary = describe_model(info)
            detail = describe_model_detail(info)
            self.message.setText(summary)
            self.message.setToolTip(f"{info.path}\n{summary}")
            self.detail.setText(detail)
            self.detail.setToolTip(describe_model_detail_tooltip(info))
            set_prop(self.message, "role", "caption")
        elif reason:
            self.message.setText(reason)
            self.detail.setText("")
            set_prop(self.message, "role", "captionError")
        else:
            self.message.setText(self._hint)
            self.detail.setText("")
            set_prop(self.message, "role", "caption")
        set_prop(self.edit, "invalid", bool(reason))
        self.edit.setAccessibleDescription(reason or "")
        if info != self._info:
            self._info = info
            self.modelChanged.emit(info)
