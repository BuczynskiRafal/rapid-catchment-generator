"""The input cards of the main window.

* :class:`ModelCard`: the SWMM model (path field with its two status lines) and the
  Output choice, across the full width.
* :class:`InputsCard`: land cover, land form and area, with the primary action row
  (*Add subcatchment* and the line that explains its state) pinned to the bottom.

The cards only build and own their widgets; the window wires them to the engine, the
model and the history. Their field labels share one width (:func:`align_field_labels`),
so the fields of both cards line up.
"""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QLocale, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QButtonGroup,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from rcg.gui.categories import CategoryOption, land_cover_options, land_form_options
from rcg.gui.preview_controller import InputsKey
from rcg.gui.widgets import ModelPathField
from rcg.gui.widgets._util import ElidedLabel, WrapLabel, divider, hbox, label, set_prop
from rcg.gui.widgets.buttons import PrimaryButton
from rcg.validation import max_area_ha

__all__ = [
    "ADD_TEXT",
    "AREA_DEFAULT_HA",
    "AREA_MAX_HA",
    "AREA_MIN_HA",
    "AREA_RANGE_TEXT",
    "InputsCard",
    "ModelCard",
    "OUTPUT_COPY",
    "OUTPUT_IN_PLACE",
    "align_field_labels",
]

ADD_TEXT = "Add subcatchment"
OUTPUT_IN_PLACE = "in_place"
OUTPUT_COPY = "copy"
# The spin box shows two decimals, so its minimum is 0.01 ha, deliberately above
# min_area_ha(); the maximum is the validation limit from defaults.json.
AREA_MIN_HA, AREA_MAX_HA, AREA_DEFAULT_HA = 0.01, max_area_ha(), 1.0
AREA_RANGE_TEXT = f"{AREA_MIN_HA:g} to {AREA_MAX_HA:,.0f} ha".replace(",", " ")  # "0.01 to 10 000 ha"

_HINT_ROLE = Qt.ItemDataRole.UserRole + 1  # one-line hint of a category option


def align_field_labels(labels: Iterable[QLabel]) -> None:
    """Give every field label the same width so the fields of both cards line up."""
    labels = list(labels)
    width = max((lbl.sizeHint().width() for lbl in labels), default=0)
    for lbl in labels:
        lbl.setMinimumWidth(width)


class _Card(QFrame):
    """A titled card whose fields sit in a two-column grid (label, field)."""

    def __init__(self, title: str, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("card", True)
        self.setObjectName(name)
        self.field_labels: list[QLabel] = []
        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(3)
        self.grid.setColumnStretch(1, 1)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 14, 18, 16)
        self.body.setSpacing(10)
        self.body.addWidget(label(title, "sectionTitle", self))
        self.body.addLayout(self.grid)

    def _field_label(self, text: str, buddy: QWidget) -> QLabel:
        """Left-column label; the grid row centres it on its field."""
        lbl = label(text, "fieldLabel", self)
        lbl.setBuddy(buddy)
        self.field_labels.append(lbl)
        return lbl


class ModelCard(_Card):
    """The SWMM model to edit and where the result goes (in place, or a copy)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("SWMM model", "modelCard", parent)
        self.path_field = ModelPathField(self)

        self.in_place_radio = QRadioButton("Update model in place (backup kept)", self)
        self.in_place_radio.setToolTip(
            "Overwrite the model; the original is first copied to a .rcg_backups folder next to it."
        )
        self.copy_radio = QRadioButton("Save as copy…", self)
        self.copy_radio.setToolTip(
            "Leave the model untouched: choose a new file when you add. The copy then becomes the model you edit."
        )
        for radio in (self.in_place_radio, self.copy_radio):
            radio.setFocusPolicy(Qt.FocusPolicy.TabFocus)  # a click never leaves a focus ring
        self.output_group = QButtonGroup(self)
        self.output_group.addButton(self.in_place_radio)
        self.output_group.addButton(self.copy_radio)
        self.in_place_radio.setChecked(True)

        # Side by side at their own width (the focus ring hugs the text): the card spans
        # the window, so one row is enough and keeps the card short.
        outputs = hbox(self.in_place_radio, self.copy_radio, 1, spacing=24)

        grid = self.grid
        grid.addWidget(self._field_label("File", self.path_field.edit), 0, 0)
        grid.addWidget(self.path_field, 0, 1)
        grid.addWidget(self.path_field.message, 1, 1)
        grid.addWidget(self.path_field.detail, 2, 1)
        grid.setRowMinimumHeight(3, 6)
        grid.addWidget(self._field_label("Output", self.in_place_radio), 4, 0)
        grid.addLayout(outputs, 4, 1)

    def output_mode(self) -> str:
        return OUTPUT_COPY if self.copy_radio.isChecked() else OUTPUT_IN_PLACE

    def focus_chain(self) -> list[QWidget]:
        """The card's focusable widgets in Tab order."""
        return [self.path_field.edit, self.path_field.browse_button, self.in_place_radio, self.copy_radio]


class InputsCard(_Card):
    """Land cover, land form and area, with the *Add subcatchment* row at the bottom.

    ``inputsChanged`` fires whenever one of the three inputs changes; ``statusExpired``
    when a confirmation shown by :meth:`flash_status` has timed out.
    """

    inputsChanged = Signal()
    statusExpired = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Subcatchment", "inputsCard", parent)
        self.cover_combo = self._make_combo(land_cover_options(), "Land cover")
        self.form_combo = self._make_combo(land_form_options(), "Land form")
        # One short line each (the full description is the tooltip), so the card keeps
        # the same height for every category and fits at the minimum window size.
        self.cover_hint = ElidedLabel("", "caption", self, mode=Qt.TextElideMode.ElideRight)
        self.form_hint = ElidedLabel("", "caption", self, mode=Qt.TextElideMode.ElideRight)

        self.area_spin = QDoubleSpinBox(self)
        self.area_spin.setLocale(QLocale.c())
        self.area_spin.setDecimals(2)
        self.area_spin.setRange(AREA_MIN_HA, AREA_MAX_HA)
        self.area_spin.setValue(AREA_DEFAULT_HA)
        self.area_spin.setSuffix(" ha")
        self.area_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.area_spin.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.area_spin.setAccelerated(True)
        self.area_spin.setAccessibleName("Area in hectares")
        self.area_spin.setToolTip(f"Subcatchment area, {AREA_RANGE_TEXT}. Up and Down arrows step by 1 ha.")
        self.area_spin.setMinimumWidth(110)
        self.area_spin.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        area_caption = ElidedLabel(AREA_RANGE_TEXT, "caption", self, mode=Qt.TextElideMode.ElideRight)

        grid = self.grid
        grid.addWidget(self._field_label("Land cover", self.cover_combo), 0, 0)
        grid.addWidget(self.cover_combo, 0, 1)
        grid.addWidget(self.cover_hint, 1, 1)
        grid.setRowMinimumHeight(2, 6)
        grid.addWidget(self._field_label("Land form", self.form_combo), 3, 0)
        grid.addWidget(self.form_combo, 3, 1)
        grid.addWidget(self.form_hint, 4, 1)
        grid.setRowMinimumHeight(5, 6)
        area_row = hbox(self.area_spin, (area_caption, 1), spacing=10)  # the caption elides instead of widening the column
        grid.addWidget(self._field_label("Area", self.area_spin), 6, 0)
        grid.addLayout(area_row, 6, 1)
        # The card is as tall as the preview beside it; the action sits at the bottom.
        self.body.addStretch(1)
        self.body.addWidget(divider(self))
        self.body.addLayout(self._build_action_row())

        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self.statusExpired)

        self.cover_combo.currentIndexChanged.connect(self._on_category_changed)
        self.form_combo.currentIndexChanged.connect(self._on_category_changed)
        self.area_spin.valueChanged.connect(self.inputsChanged)
        self._on_category_changed()

    def inputs_key(self) -> InputsKey:
        """The inputs as the preview cache keys them (area rounded to what the spin box shows)."""
        return (round(self.area_spin.value(), 2), self.form_combo.currentData(), self.cover_combo.currentData())

    def focus_chain(self) -> list[QWidget]:
        """The card's focusable widgets in Tab order."""
        return [self.cover_combo, self.form_combo, self.area_spin, self.add_button]

    def show_add_state(self, *, enabled: bool, busy: bool, hint: str) -> None:
        """Enable *Add* and explain its state (*hint*), unless a confirmation is on show."""
        self.add_button.setEnabled(enabled)
        self.add_button.setText("Adding…" if busy else ADD_TEXT)
        if self._status_timer.isActive() and not busy:
            return  # a confirmation is being shown; it reverts when the timer fires
        set_prop(self.add_hint, "role", "caption")
        self.add_hint.setText(hint)
        self.add_button.setToolTip(hint if not enabled else "")

    def flash_status(self, text: str, timeout_ms: int) -> None:
        """Show a short confirmation next to the primary button (no layout shift)."""
        self._status_timer.start(timeout_ms)
        set_prop(self.add_hint, "role", "captionSuccess")
        self.add_hint.setText(text)

    def clear_status(self) -> None:
        """Drop a confirmation that no longer applies; the next state update replaces it."""
        self._status_timer.stop()

    def _make_combo(self, options: tuple[CategoryOption, ...], accessible: str) -> QComboBox:
        combo = QComboBox(self)
        combo.setAccessibleName(accessible)
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(10)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        combo.setMaxVisibleItems(len(options))
        for index, option in enumerate(options):
            combo.addItem(option.label, option.member)
            combo.setItemData(index, option.description, Qt.ItemDataRole.ToolTipRole)
            combo.setItemData(index, option.hint, _HINT_ROLE)
            combo.setItemData(index, f"{option.label}. {option.description}", Qt.ItemDataRole.AccessibleDescriptionRole)
        view = combo.view()
        view.setMinimumWidth(view.sizeHintForColumn(0) + 32)
        return combo

    def _build_action_row(self) -> QHBoxLayout:
        # Two lines are always reserved, so a longer message never changes the row's (and
        # the window's minimum) height.
        self.add_hint = WrapLabel("", "caption", self, reserve_lines=2)
        self.add_hint.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.add_button = PrimaryButton(ADD_TEXT, self)
        self.add_button.setAccessibleName(ADD_TEXT)
        self.add_button.setMinimumWidth(180)

        row = QHBoxLayout()
        row.setContentsMargins(0, 2, 0, 0)
        row.setSpacing(14)
        row.addWidget(self.add_hint, 1)
        row.addWidget(self.add_button)
        return row

    def _on_category_changed(self) -> None:
        for combo, hint in ((self.cover_combo, self.cover_hint), (self.form_combo, self.form_hint)):
            description = combo.currentData(Qt.ItemDataRole.ToolTipRole) or ""
            hint.setText(combo.currentData(_HINT_ROLE) or description)
            hint.setToolTip(description)
            combo.setToolTip(description)
            combo.setAccessibleDescription(description)
        self.inputsChanged.emit()
