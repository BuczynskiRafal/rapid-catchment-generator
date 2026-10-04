"""The single RCG window.

Layout, top to bottom: the header; the SWMM model across the full width; the inputs
(with the primary action) and the live preview side by side, always of equal height;
the session history across the full width, which takes whatever height is left.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QLocale, QMimeData, QObject, QSettings, QSize, Qt, QThreadPool, QTimer
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QIcon,
    QKeySequence,
    QShowEvent,
)
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from rcg.exceptions import RCGError
from rcg.gui.categories import CategoryOption, land_cover_options, land_form_options
from rcg.gui.file_actions import show_in_folder
from rcg.gui.help_dialog import HelpDialog
from rcg.gui.preview_controller import InputsKey, PreviewController
from rcg.gui.resources import resource_path
from rcg.gui.widgets import HistoryEntry, HistoryPanel, MessageBanner, ModelPathField, PreviewPanel
from rcg.gui.widgets._util import ElidedLabel, LayoutItem, WrapLabel, card, divider, hbox, label, set_prop, vbox
from rcg.gui.widgets.buttons import PrimaryButton
from rcg.gui.widgets.path_field import INP_FILTER
from rcg.gui.widgets.preview import PREPARING_TEXT
from rcg.gui.workers import Task
from rcg.logging_config import get_logger
from rcg.validation import max_area_ha

if TYPE_CHECKING:
    from rcg.catchment import ApplyResult, ModelInfo, SubcatchmentParameters
    from rcg.fuzzy.engine import FuzzyEngine

__all__ = ["MainWindow", "OUTPUT_COPY", "OUTPUT_IN_PLACE", "normalise_output_path"]

logger = get_logger("gui")  # one logger for the whole GUI (rcg.gui)

APP_TITLE = "Rapid Catchment Generator"
ADD_TEXT = "Add subcatchment"
ENGINE_FAILED_TEXT = "The fuzzy engine could not be started."
PREVIEW_FAILED_TEXT = "The preview could not be computed."
OUTPUT_IN_PLACE = "in_place"
OUTPUT_COPY = "copy"
CLOSE_WAIT_MS = 200
# The spin box shows two decimals, so its minimum is 0.01 ha, deliberately above
# min_area_ha(); the maximum is the validation limit from defaults.json.
AREA_MIN_HA, AREA_MAX_HA, AREA_DEFAULT_HA = 0.01, max_area_ha(), 1.0
AREA_RANGE_TEXT = f"{AREA_MIN_HA:g} to {AREA_MAX_HA:,.0f} ha".replace(",", " ")  # "0.01 to 10 000 ha"

_HINT_ROLE = Qt.ItemDataRole.UserRole + 1  # one-line hint of a category option

_KEY_GEOMETRY = "window/geometry"
_KEY_LAST_DIR = "paths/last_dir"
_KEY_OUTPUT_MODE = "output/mode"


def normalise_output_path(path: Path) -> Path:
    """Make sure *path* ends in ``.inp`` by appending it (``model_v1.1`` -> ``model_v1.1.inp``).

    The suffix is appended, never substituted: replacing it would turn a dotted name
    into a different, possibly existing, sibling file.
    """
    return path if path.suffix.lower() == ".inp" else path.with_name(f"{path.name}.inp")


def _copy_suggestion(source: Path) -> Path:
    """``<stem>_rcg.inp`` next to the source, numbered if that file already exists."""
    candidate = source.with_name(f"{source.stem}_rcg.inp")
    number = 2
    while candidate.exists() and number < 100:
        candidate = source.with_name(f"{source.stem}_rcg_{number}.inp")
        number += 1
    return candidate


class _Central(QWidget):
    """Central widget that keeps the window at least at the design minimum (860 x 560).

    The window's minimum size is otherwise left to the layout, so content that needs more
    room (a long error banner, large system fonts) grows the window instead of overlapping.
    """

    WINDOW_MINIMUM = QSize(860, 560)

    def minimumSizeHint(self) -> QSize:
        minimum = QSize(self.WINDOW_MINIMUM)
        window = self.window()
        bar = window.menuWidget() if isinstance(window, QMainWindow) else None
        if isinstance(bar, QMenuBar) and not bar.isNativeMenuBar():
            minimum.setHeight(minimum.height() - bar.sizeHint().height())  # the bar is part of the window
        return super().minimumSizeHint().expandedTo(minimum)


class _VerticalScrollArea(QScrollArea):
    """Scrolls vertically only, never narrower than its content.

    Its minimum height is the content's, so the cards are fully visible at the window's
    minimum size and the scroll bar never appears. Only when that would not fit on the
    screen (very large fonts, small displays) does it fall back to scrolling, and only
    then is room for the scroll bar reserved. It asks for no more than its content's
    height either, so any extra window height goes to the history below it.
    """

    SCREEN_SHARE = 0.6  # at most this share of the screen height is claimed as minimum

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def setWidget(self, widget: QWidget) -> None:
        super().setWidget(widget)
        widget.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # QScrollArea does not pass size changes of its content on to its own parent
        # layout, which would keep using a stale (e.g. pre-style-sheet) minimum width.
        if watched is self.widget() and event.type() == QEvent.Type.LayoutRequest:
            self.updateGeometry()
        return super().eventFilter(watched, event)

    def minimumSizeHint(self) -> QSize:
        hint = super().minimumSizeHint()
        content = self.widget()
        if content is None:
            return hint
        frame = 2 * self.frameWidth()
        content_hint = content.minimumSizeHint()
        width = content_hint.width() + frame
        height = content_hint.height() + frame
        screen = self.screen()
        if screen is not None:
            cap = int(screen.availableGeometry().height() * self.SCREEN_SHARE)
            if height > cap:
                height = cap
                width += self.verticalScrollBar().sizeHint().width()
        return QSize(max(hint.width(), width), max(hint.height(), height))

    def sizeHint(self) -> QSize:
        content = self.widget()
        if content is None:
            return super().sizeHint()
        minimum = self.minimumSizeHint()
        height = max(content.sizeHint().height(), content.minimumSizeHint().height()) + 2 * self.frameWidth()
        return QSize(minimum.width(), max(minimum.height(), height))


@dataclass
class _ApplyContext:
    """Everything an Add needs, captured when the button is clicked."""

    source: Path
    output: Path | None
    key: InputsKey
    params: SubcatchmentParameters | None = None
    request_id: int | None = None  # preview request computing ``key`` for this Add

    @property
    def to_copy(self) -> bool:
        """Whether this Add writes a separate file (``output``) instead of updating ``source``."""
        return self.output is not None


class MainWindow(QMainWindow):
    """Main application window.

    Parameters
    ----------
    settings : QSettings, optional
        Where to persist geometry, last directory and output mode. Tests pass an
        INI-backed instance in a temporary directory.
    engine : FuzzyEngine, optional
        A pre-built engine (tests share one). It is still warmed up on the engine
        thread, which is quick for an engine that is already built.
    log_path : Path, optional
        Shown in the generic error message so users can find the traceback.
    """

    def __init__(
        self,
        settings: QSettings | None = None,
        *,
        engine: FuzzyEngine | None = None,
        log_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(APP_TITLE)
        self.setAcceptDrops(True)

        self._settings = settings if settings is not None else QSettings()
        self._log_path = log_path
        self._field_labels: list[QLabel] = []
        self._busy = False
        self._refocus_add = False
        self._closing = False
        self._apply_ctx: _ApplyContext | None = None
        self._model_path: Path | None = None
        self._task: Task | None = None
        self._pool = QThreadPool(self)
        self._help: HelpDialog | None = None
        self._preferred_mode = OUTPUT_IN_PLACE
        self._switching_mode = False

        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._update_add_state)

        self.preview_controller = self._create_preview_controller(engine)
        self._build_ui()
        self._build_actions()
        self._restore_settings()
        self._start_engine()
        self._update_add_state()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.shutdown)

    # ------------------------------------------------------------------ UI building
    GAP = 14  # between cards, horizontally and vertically, everywhere
    HEADER_ICON = 40

    def _build_ui(self) -> None:
        central = _Central(self)
        central.setObjectName("central")
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 18)
        root.setSpacing(self.GAP)

        root.addLayout(self._build_header(central))
        self.banner = MessageBanner(central)
        root.addWidget(self.banner)
        root.addWidget(self._build_workspace(central))

        self.history = HistoryPanel(central)
        self.history.undoRequested.connect(self.undo_entry)
        self.history.showInFolderRequested.connect(self._show_in_folder)
        root.addWidget(self.history, 1)  # the only part that grows with the window

        self.setCentralWidget(central)
        self._align_field_labels()
        self._set_tab_order()

    def _build_header(self, parent: QWidget) -> QHBoxLayout:
        title = label(APP_TITLE, "title", parent)
        title.setAccessibleName(APP_TITLE)
        subtitle = ElidedLabel("SWMM subcatchments from land form and land cover", "subtitle", parent)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.help_button = QToolButton(parent)
        self.help_button.setText("?")
        self.help_button.setProperty("role", "help")
        self.help_button.setToolTip("Help (F1)")
        self.help_button.setAccessibleName("Help")
        self.help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.help_button.clicked.connect(self.show_help)

        centred = Qt.AlignmentFlag.AlignVCenter
        icon = self._header_icon(parent)
        leading: tuple[LayoutItem, ...] = ((icon, 0, centred),) if icon is not None else ()
        titles = vbox(title, subtitle, spacing=0)
        return hbox(*leading, (titles, 1), (self.help_button, 0, centred), spacing=12)

    def _header_icon(self, parent: QWidget) -> QLabel | None:
        """The application icon, sharp on high-DPI screens; ``None`` if it is missing."""
        path = resource_path("icon.png")
        if path is None:
            return None
        size = QSize(self.HEADER_ICON, self.HEADER_ICON)
        pixmap = QIcon(str(path)).pixmap(size, self.devicePixelRatioF())
        if pixmap.isNull():
            return None
        icon = QLabel(parent)
        icon.setObjectName("appIcon")
        icon.setPixmap(pixmap)
        icon.setFixedSize(size)
        icon.setAccessibleName(APP_TITLE)
        return icon

    def _build_workspace(self, parent: QWidget) -> QScrollArea:
        """Model across the top; inputs and preview below it, side by side and level.

        The model comes first: it gates everything else, and its Output choice must stay
        in view. The inputs card stretches to the preview's height and pins the primary
        action to its bottom, so both cards end on the same line.
        """
        content = QWidget()
        content.setObjectName("inputsContent")

        self.preview = PreviewPanel(content)
        row = hbox((self._build_inputs_card(content), 1), (self.preview, 1), spacing=self.GAP)
        vbox(self._build_model_card(content), row, spacing=self.GAP, parent=content)

        self.inputs_scroll = _VerticalScrollArea(parent)
        self.inputs_scroll.setObjectName("inputsScroll")
        self.inputs_scroll.setWidgetResizable(True)
        self.inputs_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.inputs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.inputs_scroll.setWidget(content)
        self.inputs_scroll.viewport().setAutoFillBackground(False)
        content.setAutoFillBackground(False)
        return self.inputs_scroll

    def _make_combo(self, parent: QWidget, options: tuple[CategoryOption, ...], accessible: str) -> QComboBox:
        combo = QComboBox(parent)
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

    def _new_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(3)
        grid.setColumnStretch(1, 1)
        return grid

    @staticmethod
    def _card_layout(box: QWidget, title: QLabel, grid: QGridLayout) -> QVBoxLayout:
        layout = QVBoxLayout(box)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addLayout(grid)
        return layout

    def _build_model_card(self, parent: QWidget) -> QWidget:
        box = card(parent, "modelCard")
        title = label("SWMM model", "sectionTitle", box)

        self.path_field = ModelPathField(box)
        self.path_field.modelChanged.connect(self._on_model_changed)

        self.in_place_radio = QRadioButton("Update model in place (backup kept)", box)
        self.in_place_radio.setToolTip(
            "Overwrite the model; the original is first copied to a .rcg_backups folder next to it."
        )
        self.copy_radio = QRadioButton("Save as copy…", box)
        self.copy_radio.setToolTip(
            "Leave the model untouched: choose a new file when you add. The copy then becomes the model you edit."
        )
        for radio in (self.in_place_radio, self.copy_radio):
            radio.setFocusPolicy(Qt.FocusPolicy.TabFocus)  # a click never leaves a focus ring
        self.output_group = QButtonGroup(self)
        self.output_group.addButton(self.in_place_radio)
        self.output_group.addButton(self.copy_radio)
        self.in_place_radio.setChecked(True)
        self.output_group.buttonToggled.connect(self._on_output_mode_changed)

        # Side by side at their own width (the focus ring hugs the text): the card spans
        # the window, so one row is enough and keeps the card short.
        outputs = hbox(self.in_place_radio, self.copy_radio, 1, spacing=24)

        grid = self._new_grid()
        grid.addWidget(self._field_label("File", self.path_field.edit, box), 0, 0)
        grid.addWidget(self.path_field, 0, 1)
        grid.addWidget(self.path_field.message, 1, 1)
        grid.addWidget(self.path_field.detail, 2, 1)
        grid.setRowMinimumHeight(3, 6)
        grid.addWidget(self._field_label("Output", self.in_place_radio, box), 4, 0)
        grid.addLayout(outputs, 4, 1)
        self._card_layout(box, title, grid)
        return box

    def _build_inputs_card(self, parent: QWidget) -> QWidget:
        box = card(parent, "inputsCard")
        title = label("Subcatchment", "sectionTitle", box)

        self.cover_combo = self._make_combo(box, land_cover_options(), "Land cover")
        self.form_combo = self._make_combo(box, land_form_options(), "Land form")
        # One short line each (the full description is the tooltip), so the card keeps
        # the same height for every category and fits at the minimum window size.
        self.cover_hint = ElidedLabel("", "caption", box, mode=Qt.TextElideMode.ElideRight)
        self.form_hint = ElidedLabel("", "caption", box, mode=Qt.TextElideMode.ElideRight)

        self.area_spin = QDoubleSpinBox(box)
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
        area_caption = ElidedLabel(AREA_RANGE_TEXT, "caption", box, mode=Qt.TextElideMode.ElideRight)

        grid = self._new_grid()
        grid.addWidget(self._field_label("Land cover", self.cover_combo, box), 0, 0)
        grid.addWidget(self.cover_combo, 0, 1)
        grid.addWidget(self.cover_hint, 1, 1)
        grid.setRowMinimumHeight(2, 6)
        grid.addWidget(self._field_label("Land form", self.form_combo, box), 3, 0)
        grid.addWidget(self.form_combo, 3, 1)
        grid.addWidget(self.form_hint, 4, 1)
        grid.setRowMinimumHeight(5, 6)
        area_row = hbox(self.area_spin, (area_caption, 1), spacing=10)  # the caption elides instead of widening the column
        grid.addWidget(self._field_label("Area", self.area_spin, box), 6, 0)
        grid.addLayout(area_row, 6, 1)
        layout = self._card_layout(box, title, grid)
        # The card is as tall as the preview beside it; the action sits at the bottom.
        layout.addStretch(1)
        layout.addWidget(divider(box))
        layout.addLayout(self._build_action_row(box))

        self.cover_combo.currentIndexChanged.connect(self._on_category_changed)
        self.form_combo.currentIndexChanged.connect(self._on_category_changed)
        self.area_spin.valueChanged.connect(self._schedule_preview)
        self._on_category_changed()
        return box

    def _field_label(self, text: str, buddy: QWidget, parent: QWidget) -> QLabel:
        """Left-column label; the grid row centres it on its field."""
        lbl = label(text, "fieldLabel", parent)
        lbl.setBuddy(buddy)
        self._field_labels.append(lbl)
        return lbl

    def _align_field_labels(self) -> None:
        """Give every field label the same width so the fields of both cards line up."""
        width = max((lbl.sizeHint().width() for lbl in self._field_labels), default=0)
        for lbl in self._field_labels:
            lbl.setMinimumWidth(width)

    def _build_action_row(self, parent: QWidget) -> QHBoxLayout:
        # Two lines are always reserved, so a longer message never changes the row's (and
        # the window's minimum) height.
        self.add_hint = WrapLabel("", "caption", parent, reserve_lines=2)
        self.add_hint.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.add_button = PrimaryButton(ADD_TEXT, parent)
        self.add_button.setAccessibleName(ADD_TEXT)
        self.add_button.setMinimumWidth(180)
        self.add_button.clicked.connect(self.add_subcatchment)

        row = QHBoxLayout()
        row.setContentsMargins(0, 2, 0, 0)
        row.setSpacing(14)
        row.addWidget(self.add_hint, 1)
        row.addWidget(self.add_button)
        return row

    def _set_tab_order(self) -> None:
        chain = [
            self.path_field.edit,
            self.path_field.browse_button,
            self.in_place_radio,
            self.copy_radio,
            self.cover_combo,
            self.form_combo,
            self.area_spin,
            self.add_button,
            self.help_button,
        ]
        for first, second in zip(chain, chain[1:]):
            QWidget.setTabOrder(first, second)

    def _build_actions(self) -> None:
        def shortcuts(*keys: QKeySequence | QKeySequence.StandardKey | str) -> list[QKeySequence]:
            unique: list[QKeySequence] = []
            for key in keys:
                for seq in QKeySequence.keyBindings(key) if isinstance(key, QKeySequence.StandardKey) else [QKeySequence(key)]:
                    if not seq.isEmpty() and seq not in unique:
                        unique.append(seq)
            return unique

        self.open_action = QAction("Open Model…", self)
        self.open_action.setShortcuts(shortcuts(QKeySequence.StandardKey.Open))
        self.open_action.triggered.connect(self.path_field.browse)

        self.add_action = QAction("Add Subcatchment", self)
        self.add_action.setShortcuts(shortcuts("Ctrl+Return", "Ctrl+Enter"))
        self.add_action.triggered.connect(self.add_subcatchment)

        quit_action = QAction("Quit", self)
        quit_action.setMenuRole(QAction.MenuRole.QuitRole)
        quit_action.setShortcuts(shortcuts(QKeySequence.StandardKey.Quit))
        quit_action.triggered.connect(self.close)

        self.help_action = QAction("Rapid Catchment Generator Help", self)
        self.help_action.setShortcuts(shortcuts("F1", QKeySequence.StandardKey.HelpContents))
        self.help_action.triggered.connect(self.show_help)

        about_action = QAction("About Rapid Catchment Generator", self)
        about_action.setMenuRole(QAction.MenuRole.AboutRole)
        about_action.triggered.connect(self.show_about)

        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.add_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self.help_action)
        help_menu.addAction(about_action)

        open_hint = self.open_action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
        self.path_field.browse_button.setToolTip(f"Open a SWMM model ({open_hint})" if open_hint else "Open a SWMM model")

    # ------------------------------------------------------------------ settings
    def _restore_settings(self) -> None:
        geometry = self._settings.value(_KEY_GEOMETRY)
        if geometry is None or not self.restoreGeometry(geometry):
            self.resize(self._default_size())
        last_dir = str(self._settings.value(_KEY_LAST_DIR, "", type=str) or "")
        if last_dir:
            self.path_field.set_start_directory(last_dir)
        if str(self._settings.value(_KEY_OUTPUT_MODE, OUTPUT_IN_PLACE, type=str)) == OUTPUT_COPY:
            self.copy_radio.setChecked(True)

    def _default_size(self) -> QSize:
        wanted = QSize(1120, 820).expandedTo(self.minimumSizeHint())
        screen = self.screen()
        if screen is not None:
            available = screen.availableGeometry().size() * 0.9
            wanted = wanted.boundedTo(available).expandedTo(self.minimumSize())
        return wanted

    def _save_settings(self) -> None:
        self._settings.setValue(_KEY_GEOMETRY, self.saveGeometry())
        self._settings.setValue(_KEY_OUTPUT_MODE, self._preferred_mode)
        self._settings.sync()

    def _remember_directory(self, path: Path) -> None:
        directory = str(Path(path).parent)
        self._settings.setValue(_KEY_LAST_DIR, directory)
        self.path_field.set_start_directory(directory)

    # ------------------------------------------------------------------ engine & preview
    def _create_preview_controller(self, engine: FuzzyEngine | None) -> PreviewController:
        # Created before the UI: building the inputs already schedules a preview.
        controller = PreviewController(self._inputs_key, engine=engine, parent=self)
        controller.engineReady.connect(self._update_add_state)
        controller.engineFailed.connect(self._on_engine_failed)
        controller.previewReady.connect(self._on_preview_ready)
        controller.previewFailed.connect(self._on_preview_failed)
        controller.pinnedReady.connect(self._on_pinned_ready)
        controller.pinnedFailed.connect(self._on_pinned_failed)
        return controller

    def _start_engine(self) -> None:
        self.preview.show_preparing()
        self.preview_controller.start()

    @property
    def engine_ready(self) -> bool:
        return self.preview_controller.ready

    def _on_engine_failed(self, exc: BaseException) -> None:
        if self._closing:
            return
        self.preview.show_unavailable(ENGINE_FAILED_TEXT)
        self.banner.show_error(self._describe_error(exc, ENGINE_FAILED_TEXT))
        self._update_add_state()

    def _inputs_key(self) -> InputsKey:
        return (round(self.area_spin.value(), 2), self.form_combo.currentData(), self.cover_combo.currentData())

    def _schedule_preview(self) -> None:
        self.preview_controller.schedule()

    def _on_preview_ready(self, _key: InputsKey, params: SubcatchmentParameters) -> None:
        self.preview.show_parameters(params)

    def _on_preview_failed(self, exc: BaseException) -> None:
        self.preview.show_error(self._describe_error(exc, PREVIEW_FAILED_TEXT))

    def _on_pinned_ready(self, request_id: int, params: SubcatchmentParameters) -> None:
        ctx = self._apply_ctx
        if ctx is not None and ctx.request_id == request_id:
            self._start_apply(params)

    def _on_pinned_failed(self, request_id: int, exc: BaseException) -> None:
        ctx = self._apply_ctx
        if ctx is not None and ctx.request_id == request_id:
            self.banner.show_error(self._describe_error(exc, PREVIEW_FAILED_TEXT))
            self._finish_apply()

    def current_parameters(self) -> SubcatchmentParameters | None:
        """Parameters shown in the preview, if they match the current inputs."""
        return self.preview_controller.parameters_for(self._inputs_key())

    # ------------------------------------------------------------------ input handlers
    def _on_category_changed(self) -> None:
        for combo, hint in ((self.cover_combo, self.cover_hint), (self.form_combo, self.form_hint)):
            description = combo.currentData(Qt.ItemDataRole.ToolTipRole) or ""
            hint.setText(combo.currentData(_HINT_ROLE) or description)
            hint.setToolTip(description)
            combo.setToolTip(description)
            combo.setAccessibleDescription(description)
        self._schedule_preview()

    def _on_model_changed(self, info: ModelInfo | None) -> None:
        path = info.path if info is not None else None
        if path != self._model_path:
            self._model_path = path
            self._status_timer.stop()  # a stale "Added ..." confirmation would be misleading now
            if path is not None:
                self._remember_directory(path)
        self.preview.set_model(info)
        self._update_add_state()

    def _on_output_mode_changed(self) -> None:
        if not self._switching_mode:  # only the user's own choice is remembered
            self._preferred_mode = self.output_mode()
            self._settings.setValue(_KEY_OUTPUT_MODE, self._preferred_mode)

    def output_mode(self) -> str:
        return OUTPUT_COPY if self.copy_radio.isChecked() else OUTPUT_IN_PLACE

    def _update_add_state(self) -> None:
        has_model = self.path_field.path() is not None
        enabled = self.preview_controller.ready and has_model and not self._busy
        self.add_button.setEnabled(enabled)
        self.add_action.setEnabled(enabled)
        self.add_button.setText("Adding…" if self._busy else ADD_TEXT)

        if self._status_timer.isActive() and not self._busy:
            return  # a confirmation is being shown; it reverts when the timer fires
        set_prop(self.add_hint, "role", "caption")
        hint = self._add_hint(has_model)
        self.add_hint.setText(hint)
        self.add_button.setToolTip(hint if not enabled else "")

    def _add_hint(self, has_model: bool) -> str:
        """The line under *Add subcatchment*: why it is disabled, or its shortcut."""
        if self._busy:
            return "Writing the model…"
        if self.preview_controller.failed:
            return "The fuzzy engine is not available."
        if not self.preview_controller.ready:
            return PREPARING_TEXT
        if not has_model:
            return "Fix the model path first." if self.path_field.text().strip() else "Choose a SWMM model first."
        shortcut = self.add_action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
        return f"Press {shortcut} to add" if shortcut else ""

    # ------------------------------------------------------------------ add / undo
    def add_subcatchment(self) -> None:
        """Write the subcatchment for the inputs as they are now (later edits do not leak in)."""
        source = self.path_field.path()
        if self._busy or not self.preview_controller.ready or source is None:
            return
        output: Path | None = None
        if self.copy_radio.isChecked():
            output = self._choose_output_path(source)
            if output is None:
                return
            if output.resolve() == source.resolve():
                output = None
        self.banner.dismiss()
        # Disabling the button while busy moves keyboard focus away; give it back afterwards.
        self._refocus_add = self.add_button.hasFocus()
        key = self._inputs_key()
        ctx = _ApplyContext(source=source, output=output, key=key)
        self._apply_ctx = ctx
        self._set_busy(True)

        params = self.preview_controller.lookup(key)
        if params is not None:
            self._start_apply(params)
        else:
            ctx.request_id = self.preview_controller.pin(key)

    def _choose_output_path(self, source: Path) -> Path | None:
        """Ask where to save the copy; ``None`` when cancelled."""
        chosen = self._ask_save_path(_copy_suggestion(source))
        if not chosen:
            return None
        confirmed = Path(chosen)
        path = normalise_output_path(confirmed)
        if path != confirmed and path.exists() and not self._confirm_replace(path):
            return None
        return path

    def _ask_save_path(self, suggestion: Path) -> str | None:
        """Run the save dialog (separate method so tests can replace it)."""
        dialog = QFileDialog(self, "Save model as", str(suggestion.parent), INP_FILTER)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setDefaultSuffix("inp")
        dialog.selectFile(str(suggestion))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        files = dialog.selectedFiles()
        return files[0] if files else None

    def _confirm_replace(self, path: Path) -> bool:
        """Ask before overwriting a file the save dialog did not confirm."""
        answer = QMessageBox.question(
            self,
            "Replace file?",
            f"{path.name} already exists in {path.parent}.\nDo you want to replace it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _start_apply(self, params: SubcatchmentParameters) -> None:
        ctx = self._apply_ctx
        if ctx is None or ctx.params is not None:
            return
        ctx.params = params
        from rcg import service  # light: does not load the fuzzy engine

        task = Task(service.apply, ctx.source, params, output_path=ctx.output, backup=True)
        task.signals.succeeded.connect(self._on_apply_succeeded)
        task.signals.failed.connect(self._on_apply_failed)
        task.signals.finished.connect(self._on_apply_finished)
        self._task = task
        self._pool.start(task)

    def _on_apply_succeeded(self, result: ApplyResult) -> None:
        ctx = self._apply_ctx
        params = ctx.params if ctx is not None else None
        output_path = Path(result.output_path)
        entry = HistoryEntry(
            subcatchment_ids=tuple(result.subcatchment_ids),
            area_ha=params.area_ha if params is not None else float("nan"),
            catchment_type=params.catchment_type if params is not None else "",
            output_path=output_path,
            backup_path=Path(result.backup_path) if result.backup_path is not None else None,
            written_sha256=result.written_sha256,
        )
        self.history.add_entry(entry)
        logger.info("Added %s to %s (backup: %s)", entry.title, output_path, entry.backup_path)
        if ctx is not None and ctx.to_copy:
            # Keep working on the copy: the next Add must build on it, not on the
            # untouched original (which would silently drop this subcatchment).
            self._switch_to(output_path)
            self.flash_status(f"Added {entry.title}. Now editing {output_path.name}")
        else:
            self._remember_directory(output_path)
            self.flash_status(f"Added {entry.title} to {output_path.name}")

    def _switch_to(self, path: Path) -> None:
        """Make *path* the edited model, updated in place from now on."""
        self._switching_mode = True
        try:
            self.in_place_radio.setChecked(True)
        finally:
            self._switching_mode = False
        self.path_field.set_path(path)

    def _on_apply_failed(self, exc: BaseException) -> None:
        if not isinstance(exc, RCGError):
            self._log_unexpected("Adding the subcatchment failed", exc)
        self.banner.show_error(self._describe_error(exc, "The subcatchment could not be added."))

    def _on_apply_finished(self) -> None:
        # The finished task stays referenced in self._task until the next apply replaces it,
        # so its signal object is never destroyed while a signal is being delivered.
        self._finish_apply()

    def _finish_apply(self) -> None:
        self._apply_ctx = None
        self._set_busy(False)
        self.path_field.revalidate()
        if self._refocus_add and self.add_button.isEnabled():
            self.add_button.setFocus(Qt.FocusReason.TabFocusReason)
        self._refocus_add = False

    def _set_busy(self, busy: bool) -> None:
        if busy:
            self._status_timer.stop()  # the previous confirmation no longer applies
        self._busy = busy
        self._update_add_state()

    @property
    def busy(self) -> bool:
        return self._busy

    def undo_entry(self, entry: HistoryEntry) -> bool:
        """Restore the model from the backup taken before *entry* was added."""
        if self._busy or entry is not self.history.undo_candidate() or entry.backup_path is None:
            return False
        target, backup = entry.output_path, entry.backup_path
        from rcg import service  # light: does not load the fuzzy engine

        try:
            service.restore(backup, target, expected_sha256=entry.written_sha256)
        except RCGError as exc:
            logger.warning("Undo of %s failed: %s", entry.title, exc, exc_info=isinstance(exc.__cause__, OSError))
            self.banner.show_error(str(exc))
            return False
        entry.undone = True
        self.history.refresh()
        self.path_field.revalidate()
        self.flash_status(f"Undone: {entry.title} removed from {target.name}")
        return True

    def flash_status(self, text: str, timeout_ms: int = 6000) -> None:
        """Show a short confirmation next to the primary button (no layout shift)."""
        self._status_timer.start(timeout_ms)
        set_prop(self.add_hint, "role", "captionSuccess")
        self.add_hint.setText(text)

    def status_text(self) -> str:
        return self.add_hint.text()

    def _show_in_folder(self, path: Path) -> None:
        if not show_in_folder(path):
            self.banner.show_error(f"Could not open the folder {Path(path).parent}.")

    # ------------------------------------------------------------------ errors
    def _describe_error(self, exc: BaseException, fallback: str) -> str:
        if isinstance(exc, RCGError) and str(exc):
            return str(exc)
        where = f" Details were written to {self._log_path}." if self._log_path else " Details were written to the log."
        return f"{fallback} An unexpected error occurred.{where}"

    @staticmethod
    def _log_unexpected(message: str, exc: BaseException) -> None:
        logger.error(message, exc_info=(type(exc), exc, exc.__traceback__))

    def report_unexpected_error(self) -> None:
        """Called by the application's exception hook for errors raised in slots."""
        self.banner.show_error(self._describe_error(RuntimeError(), "Something went wrong."))

    # ------------------------------------------------------------------ help
    def show_help(self) -> None:
        if self._help is None:
            self._help = HelpDialog(self)
        self._help.show()
        self._help.raise_()
        self._help.activateWindow()

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_TITLE}",
            f"<h3>{APP_TITLE}</h3><p>Version {_version()}</p>"
            "<p>Rapid prototyping of SWMM subcatchments with fuzzy logic.</p>"
            '<p><a href="https://github.com/BuczynskiRafal/rapid-catchment-generator">'
            "github.com/BuczynskiRafal/rapid-catchment-generator</a><br>MIT License</p>",
        )

    # ------------------------------------------------------------------ drag & drop
    @staticmethod
    def _dropped_file(mime: QMimeData) -> str | None:
        if not mime.hasUrls():
            return None
        for url in mime.urls():
            if url.isLocalFile():
                return url.toLocalFile()
        return None

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._dropped_file(event.mimeData()):
            event.acceptProposedAction()
            self.path_field.set_drop_highlight(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._dropped_file(event.mimeData()):
            event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.path_field.set_drop_highlight(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self.path_field.set_drop_highlight(False)
        filename = self._dropped_file(event.mimeData())
        if filename:
            event.acceptProposedAction()
            self.open_model(filename)

    def open_model(self, path: str | Path) -> None:
        """Make *path* the edited model (dropped file, "Open with", command-line argument).

        Once the window is shown it is also brought to the front with the path field
        focused, so the user sees the model check right away.
        """
        self.path_field.set_path(path)
        if self.isVisible():
            self.path_field.edit.setFocus(Qt.FocusReason.OtherFocusReason)
            self.raise_()
            self.activateWindow()

    # ------------------------------------------------------------------ showing
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        # Showing applies the style sheet, which widens the inputs. Qt would pass that on
        # in two event-loop passes (the scroll area's cached size, then every layout above
        # it), so until then the window's minimum size would be stale and later jump.
        # Do both now: the minimum size is final as soon as the window is shown.
        self.inputs_scroll.updateGeometry()
        central = self.centralWidget()
        if central is not None and (central_layout := central.layout()) is not None:
            _invalidate_layouts(central_layout)
        if (window_layout := self.layout()) is not None:
            window_layout.invalidate()

    # ------------------------------------------------------------------ shutdown
    def closeEvent(self, event: QCloseEvent) -> None:
        self._closing = True
        self._save_settings()
        if self._help is not None:
            self._help.close()
        # Disappear at once. A warm-up in progress cannot be interrupted, so the wait is
        # short; the thread then finishes in the background and is waited for when the
        # application quits (or when this window is destroyed), never torn down running.
        self.hide()
        self.preview_controller.close()
        self.shutdown(wait_ms=CLOSE_WAIT_MS)
        super().closeEvent(event)

    def shutdown(self, wait_ms: int | None = None) -> None:
        """Stop background work, waiting at most *wait_ms* (``None``: until it is done)."""
        self.preview_controller.shutdown(wait_ms)
        if wait_ms is None:
            self._pool.waitForDone()
        else:
            self._pool.waitForDone(wait_ms)

    def engine_thread_running(self) -> bool:
        return self.preview_controller.thread_running()


def _invalidate_layouts(layout: QLayout) -> None:
    """Drop the cached sizes of *layout* and every layout nested in it (innermost first)."""
    for index in range(layout.count()):
        item = layout.itemAt(index)
        child = item.layout() if item is not None else None
        if child is not None:
            _invalidate_layouts(child)
    layout.invalidate()


def _version() -> str:
    import rcg

    version = getattr(rcg, "__version__", None)
    if version:
        return str(version)
    try:
        from importlib.metadata import version as dist_version

        return dist_version("rapid-catchment-generator")
    except Exception:  # not installed (e.g. running from a checkout)
        return "unknown"
