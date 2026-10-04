"""Live preview of the computed SWMM subcatchment parameters."""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from rcg.catchment import INFILTRATION_FIELDS, infiltration_for
from rcg.gui.categories import CATCHMENT_TYPE_LABELS, catchment_type_label, infiltration_method_label
from rcg.gui.widgets._util import ElidedLabel, ReservedLabel, WrapLabel, divider, label

if TYPE_CHECKING:
    from rcg.catchment import ModelInfo, SubcatchmentParameters

__all__ = ["DEFAULT_INFILTRATION_METHOD", "PreviewPanel", "format_number"]

DEFAULT_INFILTRATION_METHOD = "GREEN_AMPT"
"""Shown while no model is chosen (RCG 1.x always wrote Green-Ampt)."""

NO_MODEL_INFILTRATION_NOTE = "Green-Ampt until a model is chosen"
NO_MODEL_INFILTRATION_TOOLTIP = (
    "Without a model the Green-Ampt row is shown. The infiltration method, and with it the "
    "fields and their units, is taken from the model you choose."
)

_DASH = "—"
_NO_UNIT = "–"  # INFILTRATION_FIELDS marks dimensionless values with an en dash


def format_number(value: float, decimals: int = 2) -> str:
    """Locale-neutral fixed-point formatting (``1234.5 -> "1234.50"``)."""
    return f"{value:.{decimals}f}"


def _format_compact(value: float) -> str:
    """Up to 2 decimals without trailing zeros (``3.50 -> "3.5"``, ``7.0 -> "7"``)."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _with_unit(value: str, unit: str) -> str:
    return value if not unit or unit == _NO_UNIT else f"{value} {unit}"


_MAX_INFILTRATION_COLUMNS = max(len(fields) for fields in INFILTRATION_FIELDS.values())

# The widest text each value can show: slope and imperviousness stay below 100 % (the
# centroid of the fuzzy output never reaches the end of its 0-60 / 0-100 universe),
# the width of 10 000 ha is 5000 m, Manning's n < 1, storage a few mm. The labels
# reserve this room from the start, so values arriving after warm-up never widen the
# window (a wider text would still get its room rather than be clipped).
_PERCENT_SAMPLES = ("00.00",)
_WIDTH_SAMPLES = ("0000.00",)
_N_SAMPLES = ("0.000",)
_STORAGE_SAMPLES = ("00.00 mm",)
_PCT_ZERO_SAMPLES = ("100 %",)


@cache
def _infiltration_texts(method: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """``(header, every value text)`` per labelled column of *method*, in SI, US and no units.

    Cached: the size hints that use it are queried on every layout pass.
    """
    values = list(infiltration_for(method).items())
    return tuple(
        (key, tuple(_with_unit(_format_compact(float(value)), unit) for unit in (si_unit, us_unit, "")))
        for (_name, si_unit, us_unit), (key, value) in zip(INFILTRATION_FIELDS[method], values)
    )


class _Metric(QWidget):
    """Caption above a large value with its unit.

    The widget reserves the width of its widest *samples* value, so the unit stays right
    next to the number while the layout never changes when the value does.
    """

    VALUE_UNIT_SPACING = 4

    def __init__(
        self, caption: str, unit: str, parent: QWidget | None = None, *, tooltip: str = "", samples: tuple[str, ...] = ()
    ) -> None:
        super().__init__(parent)
        self._samples = samples
        self.value = label(_DASH, "metricValue", self)
        self.value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.unit = label(unit, "metricUnit", self)
        self.caption = label(caption, "metricLabel", self)
        if tooltip:
            self.setToolTip(tooltip)

        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(self.VALUE_UNIT_SPACING)
        value_row.addWidget(self.value, 0, Qt.AlignmentFlag.AlignBaseline)
        value_row.addWidget(self.unit, 0, Qt.AlignmentFlag.AlignBaseline)
        value_row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.caption)
        layout.addLayout(value_row)

    def set_value(self, text: str) -> None:
        self.value.setText(text)
        self.setAccessibleName(f"{self.caption.text()}: {text} {self.unit.text()}".strip())

    def _reserved_width(self) -> int:
        for widget in (self.value, self.unit, self.caption):
            widget.ensurePolished()
        metrics = self.value.fontMetrics()
        value = max((metrics.horizontalAdvance(text) for text in self._samples), default=0) + 2
        return max(value + self.VALUE_UNIT_SPACING + self.unit.sizeHint().width(), self.caption.sizeHint().width())

    def minimumSizeHint(self) -> QSize:
        hint = super().minimumSizeHint()
        return QSize(max(hint.width(), self._reserved_width()), hint.height())

    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        return QSize(max(hint.width(), self._reserved_width()), hint.height())


class _InfiltrationRow(QWidget):
    """The ``[INFILTRATION]`` values: SWMM field name above each value with its unit.

    Each column is as wide as its own content. The row's minimum width is that of the
    widest method, so choosing a model with another method or other units never changes
    the panel's (or the window's) size.
    """

    SPACING = 10

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(self.SPACING)
        self._grid.setVerticalSpacing(2)
        self.headers: list[ReservedLabel] = []
        self.values: list[ReservedLabel] = []
        for column in range(_MAX_INFILTRATION_COLUMNS):
            header = ReservedLabel("", "tableHeader", self)
            value = ReservedLabel("", "value", self)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._grid.addWidget(header, 0, column)
            self._grid.addWidget(value, 1, column)
            self._grid.setColumnStretch(column, 1)
            self.headers.append(header)
            self.values.append(value)

    def set_method(self, method: str, info: ModelInfo | None) -> None:
        """Show the row RCG writes for *method*, with units when the model (*info*) is known."""
        texts = _infiltration_texts(method)
        values = list(infiltration_for(method).values())
        for column, (header, value) in enumerate(zip(self.headers, self.values)):
            if column >= len(texts):
                header.set_samples(())
                value.set_samples(())
                for widget in (header, value):
                    widget.setText("")
                    widget.setToolTip("")
                value.setAccessibleName("")
                continue
            key, samples = texts[column]
            name, si_unit, us_unit = INFILTRATION_FIELDS[method][column]
            unit = "" if info is None else (si_unit if info.is_metric else us_unit)
            shown_unit = "" if unit == _NO_UNIT else unit
            text = _with_unit(_format_compact(float(values[column])), unit)
            tooltip = f"{name} (SWMM: {key})" + (f", {shown_unit}" if shown_unit else "")
            header.set_samples((key,))
            value.set_samples(samples)  # all unit variants: switching SI/US keeps the width
            header.setText(key)
            value.setText(text)
            for widget in (header, value):
                widget.setToolTip(tooltip)
            value.setAccessibleName(f"{name}: {text}")

    def _widest_method_width(self) -> int:
        header_metrics = self.headers[0].fontMetrics()
        value_metrics = self.values[0].fontMetrics()
        widest = 0
        for method in INFILTRATION_FIELDS:
            columns = _infiltration_texts(method)
            total = sum(
                max(header_metrics.horizontalAdvance(key), *(value_metrics.horizontalAdvance(t) for t in samples)) + 2
                for key, samples in columns
            )
            widest = max(widest, total + self.SPACING * (len(columns) - 1))
        return widest

    def minimumSizeHint(self) -> QSize:
        self.ensurePolished()
        for widget in (self.headers[0], self.values[0]):
            widget.ensurePolished()
        hint = super().minimumSizeHint()
        return QSize(max(hint.width(), self._widest_method_width()), hint.height())

    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        return QSize(max(hint.width(), self.minimumSizeHint().width()), hint.height())

    def text_by_field(self) -> dict[str, str]:
        return {header.text(): value.text() for header, value in zip(self.headers, self.values) if header.text()}


class PreviewPanel(QFrame):
    """Card showing the catchment type and all parameters that will be written.

    Every cell exists from construction (``—`` until the first result), so the
    panel's size, and with it the window's minimum size, does not change when the
    engine becomes ready or a model with another infiltration method is chosen.
    """

    PAGE_PREPARING, PAGE_RESULT = 0, 1

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("card", True)
        self.setObjectName("previewPanel")
        self.setAccessibleName("Preview")
        self.parameters: SubcatchmentParameters | None = None
        self._model: ModelInfo | None = None

        title = label("Preview", "sectionTitle", self)
        self.badge = ReservedLabel("", "badge", self, samples=CATCHMENT_TYPE_LABELS.values())
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setAccessibleName("Catchment type")
        self.badge.hide()

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.badge)
        # The badge comes and goes; it keeps its place so the card never jumps.
        policy = self.badge.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.badge.setSizePolicy(policy)
        self.badge.setText(catchment_type_label("suburban"))

        self.stack = QStackedWidget(self)
        self.stack.addWidget(self._build_preparing_page())
        self.stack.addWidget(self._build_result_page())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(12)
        layout.addLayout(header)
        layout.addWidget(self.stack)
        # Never shrink below the content: a long banner grows the window instead. It may
        # grow, to stay level with the inputs card beside it.
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.set_model(None)
        self.show_preparing()

    # -- pages -----------------------------------------------------------------------
    def _build_preparing_page(self) -> QWidget:
        page = QWidget(self)
        self.preparing_label = label("Preparing fuzzy engine…", "placeholder", page)
        self.preparing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preparing_detail = WrapLabel(
            "Building the fuzzy rule base takes a few seconds the first time. Inputs stay editable meanwhile.",
            "caption",
            page,
        )
        self.preparing_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress = QProgressBar(page)
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setMaximumWidth(220)
        self.progress.setAccessibleName("Preparing fuzzy engine")

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addStretch(1)
        layout.addWidget(self.preparing_label)
        layout.addWidget(self.progress, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.preparing_detail)
        layout.addStretch(1)
        return page

    def _build_result_page(self) -> QWidget:
        page = QWidget(self)

        self.slope = _Metric("Slope", "%", page, tooltip="Average surface slope (SWMM: %Slope)", samples=_PERCENT_SAMPLES)
        self.impervious = _Metric(
            "Imperviousness", "%", page, tooltip="Impervious share of the area (SWMM: %Imperv)", samples=_PERCENT_SAMPLES
        )
        self.width_metric = _Metric(
            "Width", "m", page, tooltip="Characteristic width of overland flow (SWMM: Width)", samples=_WIDTH_SAMPLES
        )
        metrics = QHBoxLayout()
        metrics.setContentsMargins(0, 0, 0, 0)
        metrics.setSpacing(12)
        for metric in (self.slope, self.impervious, self.width_metric):
            metrics.addWidget(metric, 1)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 2)
        grid.addWidget(label("", "tableHeader", page), 0, 0)
        grid.addWidget(label("Impervious", "tableHeader", page), 0, 1)
        grid.addWidget(label("Pervious", "tableHeader", page), 0, 2)

        def value_label(swmm_field: str, samples: tuple[str, ...]) -> QLabel:
            lbl = ReservedLabel(_DASH, "value", page, samples=samples)
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl.setToolTip(f"SWMM: {swmm_field}")
            return lbl

        self.n_imperv = value_label("N-Imperv", _N_SAMPLES)
        self.n_perv = value_label("N-Perv", _N_SAMPLES)
        self.s_imperv = value_label("Dstore-Imperv", _STORAGE_SAMPLES)
        self.s_perv = value_label("Dstore-Perv", _STORAGE_SAMPLES)
        self.pct_zero = value_label("%Zero-Imperv", _PCT_ZERO_SAMPLES)
        manning = label("Manning’s n", "fieldLabel", page)
        manning.setToolTip("Manning roughness for overland flow (SWMM: N-Imperv, N-Perv)")
        storage = label("Depression storage", "fieldLabel", page)
        storage.setToolTip("Depth of depression storage (SWMM: Dstore-Imperv, Dstore-Perv)")
        zero = label("Zero-storage share", "fieldLabel", page)
        zero.setToolTip("Percent of the impervious area with no depression storage (SWMM: %Zero-Imperv)")
        rows = ((manning, self.n_imperv, self.n_perv), (storage, self.s_imperv, self.s_perv), (zero, self.pct_zero, None))
        for row, (caption, left, right) in enumerate(rows, start=1):
            grid.addWidget(caption, row, 0)
            grid.addWidget(left, row, 1)
            if right is not None:
                grid.addWidget(right, row, 2)

        # Infiltration: its own sub-header, then one column per labelled value. All
        # cells exist up front; the row reserves the width of the widest method.
        infiltration_title = label("Infiltration", "fieldLabel", page)
        infiltration_title.setToolTip("The [INFILTRATION] row written for the new subcatchment")
        self.infiltration_note = ElidedLabel("", "caption", page, mode=Qt.TextElideMode.ElideRight)
        self.infiltration_note.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        infiltration_header = QHBoxLayout()
        infiltration_header.setContentsMargins(0, 0, 0, 0)
        infiltration_header.setSpacing(12)
        infiltration_header.addWidget(infiltration_title)
        infiltration_header.addWidget(self.infiltration_note, 1)

        self.infiltration_row = _InfiltrationRow(page)

        self.error = WrapLabel("", "captionError", page)
        self.error.hide()

        infiltration = QVBoxLayout()
        infiltration.setContentsMargins(0, 0, 0, 0)
        infiltration.setSpacing(4)
        infiltration.addLayout(infiltration_header)
        infiltration.addWidget(self.infiltration_row)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addLayout(metrics)
        layout.addWidget(divider(page))
        layout.addLayout(grid)
        layout.addWidget(divider(page))
        layout.addLayout(infiltration)
        layout.addWidget(self.error)
        layout.addStretch(1)
        return page

    # -- model -----------------------------------------------------------------------
    def set_model(self, info: ModelInfo | None) -> None:
        """Show the infiltration row the chosen model will get (Green-Ampt without one)."""
        self._model = info
        method = info.infiltration_method if info is not None else DEFAULT_INFILTRATION_METHOD
        if info is None:
            self.infiltration_note.setText(NO_MODEL_INFILTRATION_NOTE)
            self.infiltration_note.setToolTip(NO_MODEL_INFILTRATION_TOOLTIP)
        else:
            units = "SI" if info.is_metric else "US"
            self.infiltration_note.setText(f"{infiltration_method_label(method)}, from the model")
            self.infiltration_note.setToolTip(
                f"The model uses {infiltration_method_label(method)} infiltration ({method}) in {units} units "
                f"({info.flow_units}); the new subcatchment gets this row."
            )
        self.infiltration_row.set_method(method, info)

    @property
    def model(self) -> ModelInfo | None:
        return self._model

    # -- states ----------------------------------------------------------------------
    def show_preparing(self, text: str = "Preparing fuzzy engine…") -> None:
        self._show_placeholder(text, busy=True)

    def show_unavailable(self, text: str) -> None:
        """The engine could not be built: keep the placeholder page, without progress."""
        self._show_placeholder(text, busy=False)

    def _show_placeholder(self, text: str, *, busy: bool) -> None:
        self.preparing_label.setText(text)
        self.progress.setVisible(busy)
        self.preparing_detail.setVisible(busy)
        self.badge.hide()
        self.stack.setCurrentIndex(self.PAGE_PREPARING)

    def is_preparing(self) -> bool:
        return self.stack.currentIndex() == self.PAGE_PREPARING

    def show_parameters(self, p: SubcatchmentParameters) -> None:
        self.parameters = p
        self.error.hide()
        type_label = catchment_type_label(p.catchment_type)
        self.badge.setText(type_label)
        self.badge.setToolTip(f"Catchment type from the fuzzy classifier (score {format_number(p.catchment_score)} / 100)")
        self.badge.setAccessibleDescription(type_label)
        self.badge.show()
        self.slope.set_value(format_number(p.slope_pct))
        self.impervious.set_value(format_number(p.impervious_pct))
        self.width_metric.set_value(format_number(p.width_m))
        self.n_imperv.setText(format_number(p.n_imperv, 3))
        self.n_perv.setText(format_number(p.n_perv, 3))
        self.s_imperv.setText(f"{format_number(p.s_imperv_mm)} mm")
        self.s_perv.setText(f"{format_number(p.s_perv_mm)} mm")
        self.pct_zero.setText(f"{p.pct_zero} %")
        self.stack.setCurrentIndex(self.PAGE_RESULT)

    def show_error(self, text: str) -> None:
        """Inputs are invalid: blank the numbers and explain why."""
        self.parameters = None
        self.badge.hide()
        for metric in (self.slope, self.impervious, self.width_metric):
            metric.set_value(_DASH)
        for value in (self.n_imperv, self.n_perv, self.s_imperv, self.s_perv, self.pct_zero):
            value.setText(_DASH)
        self.error.setText(text)
        self.error.show()
        self.stack.setCurrentIndex(self.PAGE_RESULT)

    def infiltration_text(self) -> dict[str, str]:
        """Displayed infiltration values by SWMM field name (for tests and accessibility)."""
        return self.infiltration_row.text_by_field()
