"""The single RCG window: model and inputs on the left, live preview and history on the right."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QLocale, QMimeData, QObject, QSettings, QSize, Qt, QThread, QThreadPool, QTimer, Signal
from PySide6.QtGui import QAction, QCloseEvent, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QKeySequence
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
from rcg.gui.file_actions import restore_backup, show_in_folder
from rcg.gui.help_dialog import HelpDialog
from rcg.gui.widgets import HistoryEntry, HistoryPanel, MessageBanner, ModelPathField, PreviewPanel
from rcg.gui.widgets._util import ElidedLabel, WrapLabel, card, label, set_prop
from rcg.gui.widgets.buttons import PrimaryButton
from rcg.gui.widgets.path_field import INP_FILTER
from rcg.gui.workers import EngineWorker, Task

if TYPE_CHECKING:
    from rcg.catchment import ApplyResult, ModelInfo, SubcatchmentParameters
    from rcg.fuzzy.categories import LandCover, LandForm
    from rcg.fuzzy.engine import FuzzyEngine

__all__ = ["MainWindow", "OUTPUT_COPY", "OUTPUT_IN_PLACE", "normalise_output_path"]

logger = logging.getLogger("rcg.gui")

APP_TITLE = "Rapid Catchment Generator"
OUTPUT_IN_PLACE = "in_place"
OUTPUT_COPY = "copy"
PREVIEW_DEBOUNCE_MS = 150
CLOSE_WAIT_MS = 200
AREA_MIN_HA, AREA_MAX_HA, AREA_DEFAULT_HA = 0.01, 10_000.0, 1.0
_CACHE_LIMIT = 512

_HINT_ROLE = Qt.ItemDataRole.UserRole + 1  # one-line hint of a category option

_KEY_GEOMETRY = "window/geometry"
_KEY_LAST_DIR = "paths/last_dir"
_KEY_OUTPUT_MODE = "output/mode"

InputsKey = tuple[float, "LandForm", "LandCover"]  # (area_ha rounded to 2 dp, land form, land cover)


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _apply_and_fingerprint(
    source: Path, params: SubcatchmentParameters, output: Path | None
) -> tuple[ApplyResult, str | None]:
    """Worker body: write the model, then fingerprint the written file (for safe undo)."""
    from rcg import service

    result = service.apply(source, params, output_path=output, backup=True)
    return result, _sha256(Path(result.output_path))


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
    then is room for the scroll bar reserved.
    """

    SCREEN_SHARE = 0.6  # at most this share of the screen height is claimed as minimum

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


@dataclass
class _ApplyContext:
    """Everything an Add needs, captured when the button is clicked."""

    source: Path
    output: Path | None
    key: InputsKey
    to_copy: bool
    params: SubcatchmentParameters | None = None
    request_id: int | None = None  # preview request computing ``key`` for this Add


@dataclass
class _Entry(HistoryEntry):
    """History entry plus the fingerprint of the file as RCG wrote it."""

    written_sha256: str | None = None


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

    _previewRequested = Signal(int, object, bool)  # request id, InputsKey, pinned

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
        self._engine_ready = False
        self._engine_failed = False
        self._field_labels: list[QLabel] = []
        self._busy = False
        self._refocus_add = False
        self._closing = False
        self._apply_ctx: _ApplyContext | None = None
        self._request_seq = 0
        self._requests: dict[int, InputsKey] = {}
        self._cache: dict[InputsKey, SubcatchmentParameters] = {}
        self._params: SubcatchmentParameters | None = None
        self._params_key: InputsKey | None = None
        self._model_path: Path | None = None
        self._task: Task | None = None
        self._pool = QThreadPool(self)
        self._help: HelpDialog | None = None
        self._preferred_mode = OUTPUT_IN_PLACE
        self._switching_mode = False

        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._update_add_state)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(PREVIEW_DEBOUNCE_MS)
        self._debounce.timeout.connect(self._request_preview)

        self._build_ui()
        self._build_actions()
        self._restore_settings()
        self._start_engine(engine)
        self._update_add_state()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.shutdown)

    # ------------------------------------------------------------------ UI building
    def _build_ui(self) -> None:
        central = _Central(self)
        central.setObjectName("central")
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 18)
        root.setSpacing(12)

        root.addLayout(self._build_header(central))
        self.banner = MessageBanner(central)
        root.addWidget(self.banner)

        columns = QHBoxLayout()
        columns.setSpacing(16)
        columns.addLayout(self._build_left_column(central), 1)
        columns.addLayout(self._build_right_column(central), 1)
        root.addLayout(columns, 1)
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

        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 0, 0)
        header.setSpacing(14)
        header.addWidget(title, 0, Qt.AlignmentFlag.AlignBaseline)
        header.addWidget(subtitle, 1, Qt.AlignmentFlag.AlignBaseline)
        header.addWidget(self.help_button, 0, Qt.AlignmentFlag.AlignVCenter)
        return header

    def _build_left_column(self, parent: QWidget) -> QVBoxLayout:
        # The model comes first: it gates everything else, and its Output choice must
        # stay in view. The primary action is pinned underneath the cards.
        content = QWidget()
        content.setObjectName("inputsContent")
        cards = QVBoxLayout(content)
        cards.setContentsMargins(0, 0, 0, 0)
        cards.setSpacing(14)
        cards.addWidget(self._build_model_card(content))
        cards.addWidget(self._build_inputs_card(content))
        cards.addStretch(1)

        self.inputs_scroll = _VerticalScrollArea(parent)
        self.inputs_scroll.setObjectName("inputsScroll")
        self.inputs_scroll.setWidgetResizable(True)
        self.inputs_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.inputs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.inputs_scroll.setWidget(content)
        self.inputs_scroll.viewport().setAutoFillBackground(False)
        content.setAutoFillBackground(False)

        column = QVBoxLayout()
        column.setSpacing(12)
        column.addWidget(self.inputs_scroll, 1)
        column.addLayout(self._build_action_row(parent))
        return column

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
    def _card_layout(box: QWidget, title: QLabel, grid: QGridLayout) -> None:
        layout = QVBoxLayout(box)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addLayout(grid)

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

        grid = self._new_grid()
        grid.addWidget(self._field_label("File", self.path_field.edit, box), 0, 0)
        grid.addWidget(self.path_field, 0, 1)
        grid.addWidget(self.path_field.message, 1, 1)
        grid.addWidget(self.path_field.detail, 2, 1)
        grid.setRowMinimumHeight(3, 6)
        grid.addWidget(self._field_label("Output", self.in_place_radio, box), 4, 0)
        # Left-aligned at their own width, so the focus ring hugs the text.
        grid.addWidget(self.in_place_radio, 4, 1, Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self.copy_radio, 5, 1, Qt.AlignmentFlag.AlignLeft)
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
        self.area_spin.setToolTip("Subcatchment area, 0.01 to 10 000 ha. Up and Down arrows step by 1 ha.")
        self.area_spin.setMinimumWidth(110)
        self.area_spin.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        area_caption = ElidedLabel("0.01 to 10 000 ha", "caption", box, mode=Qt.TextElideMode.ElideRight)

        grid = self._new_grid()
        grid.addWidget(self._field_label("Land cover", self.cover_combo, box), 0, 0)
        grid.addWidget(self.cover_combo, 0, 1)
        grid.addWidget(self.cover_hint, 1, 1)
        grid.setRowMinimumHeight(2, 6)
        grid.addWidget(self._field_label("Land form", self.form_combo, box), 3, 0)
        grid.addWidget(self.form_combo, 3, 1)
        grid.addWidget(self.form_hint, 4, 1)
        grid.setRowMinimumHeight(5, 6)
        area_row = QHBoxLayout()
        area_row.setSpacing(10)
        area_row.addWidget(self.area_spin)
        area_row.addWidget(area_caption, 1)  # elides instead of widening the column
        grid.addWidget(self._field_label("Area", self.area_spin, box), 6, 0)
        grid.addLayout(area_row, 6, 1)
        self._card_layout(box, title, grid)

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
        self.add_button = PrimaryButton("Add subcatchment", parent)
        self.add_button.setAccessibleName("Add subcatchment")
        self.add_button.setMinimumWidth(180)
        self.add_button.clicked.connect(self.add_subcatchment)

        row = QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(self.add_hint, 1)
        row.addWidget(self.add_button)
        return row

    def _build_right_column(self, parent: QWidget) -> QVBoxLayout:
        self.preview = PreviewPanel(parent)
        self.history = HistoryPanel(parent)
        self.history.undoRequested.connect(self.undo_entry)
        self.history.showInFolderRequested.connect(self._show_in_folder)

        column = QVBoxLayout()
        column.setSpacing(14)
        column.addWidget(self.preview)
        column.addWidget(self.history, 1)
        return column

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
        wanted = QSize(1120, 740).expandedTo(self.minimumSizeHint())
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
    def _start_engine(self, engine: FuzzyEngine | None) -> None:
        self._engine_thread = QThread(self)
        self._engine_thread.setObjectName("rcg-fuzzy-engine")
        self._engine_worker = EngineWorker(engine)
        self._engine_worker.moveToThread(self._engine_thread)
        self._engine_worker.ready.connect(self._on_engine_ready)
        self._engine_worker.warmUpFailed.connect(self._on_engine_failed)
        self._engine_worker.previewReady.connect(self._on_preview_ready)
        self._engine_worker.previewFailed.connect(self._on_preview_failed)
        self._previewRequested.connect(self._engine_worker.compute)
        self._engine_thread.started.connect(self._engine_worker.warm_up)
        self._engine_thread.finished.connect(self._engine_worker.deleteLater)
        # If the window is destroyed without being closed (e.g. garbage-collected), stop
        # the thread before Qt deletes it: `destroyed` fires before children are deleted.
        self.destroyed.connect(partial(_stop_thread, self._engine_thread))
        self.preview.show_preparing()
        # Started from the event loop: the window paints first, and nothing heavy (the
        # fuzzy engine, skfuzzy) is imported before the worker thread runs.
        # (A child timer, not QTimer.singleShot: it dies with the window, so it can never
        # start the thread of a window that is already gone.)
        self._engine_start_timer = QTimer(self)
        self._engine_start_timer.setSingleShot(True)
        self._engine_start_timer.timeout.connect(self._start_engine_thread)
        self._engine_start_timer.start(0)

    def _start_engine_thread(self) -> None:
        if not self._closing:
            self._engine_thread.start()

    @property
    def engine_ready(self) -> bool:
        return self._engine_ready

    def _on_engine_ready(self) -> None:
        if self._closing:
            return
        self._engine_ready = True
        logger.info("Fuzzy engine ready")
        self._update_add_state()
        self._request_preview()

    def _on_engine_failed(self, exc: BaseException) -> None:
        self._engine_failed = True
        self._log_unexpected("Fuzzy engine warm-up failed", exc)
        if self._closing:
            return
        self.preview.show_unavailable("The fuzzy engine could not be started.")
        self.banner.show_error(self._describe_error(exc, "The fuzzy engine could not be started."))
        self._update_add_state()

    def _inputs_key(self) -> InputsKey:
        return (round(self.area_spin.value(), 2), self.form_combo.currentData(), self.cover_combo.currentData())

    def _schedule_preview(self) -> None:
        self._debounce.start()

    def _issue_request(self, key: InputsKey, *, pinned: bool) -> int:
        """Send *key* to the engine thread; a *pinned* request is never skipped as stale."""
        self._request_seq += 1
        request_id = self._request_seq
        self._engine_worker.note_request(request_id)  # supersedes unpinned requests still queued
        keep = {request_id - 1}
        if self._apply_ctx is not None and self._apply_ctx.request_id is not None:
            keep.add(self._apply_ctx.request_id)
        self._requests = {rid: k for rid, k in self._requests.items() if rid in keep}
        self._requests[request_id] = key
        self._previewRequested.emit(request_id, key, pinned)
        return request_id

    def _request_preview(self) -> None:
        """Show the preview for the current inputs (cached, or computed on the engine thread)."""
        self._debounce.stop()
        if not self._engine_ready:
            return
        key = self._inputs_key()
        cached = self._cache.get(key)
        if cached is not None:
            self._request_seq += 1  # results still in flight are now outdated
            self._engine_worker.note_request(self._request_seq)
            self._show_params(key, cached)
            return
        self._issue_request(key, pinned=False)

    def _remember(self, key: InputsKey, params: SubcatchmentParameters) -> None:
        if key not in self._cache and len(self._cache) >= _CACHE_LIMIT:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = params

    def _on_preview_ready(self, request_id: int, params: SubcatchmentParameters) -> None:
        key = self._requests.pop(request_id, None)
        if key is None:
            return
        self._remember(key, params)
        ctx = self._apply_ctx
        if ctx is not None and ctx.request_id == request_id:
            self._start_apply(params)
        if request_id == self._request_seq:
            self._show_params(key, params)

    def _on_preview_failed(self, request_id: int, exc: BaseException) -> None:
        key = self._requests.pop(request_id, None)
        if key is None:
            return
        if not isinstance(exc, RCGError):
            self._log_unexpected("Preview failed", exc)
        message = self._describe_error(exc, "The preview could not be computed.")
        ctx = self._apply_ctx
        if ctx is not None and ctx.request_id == request_id:
            self.banner.show_error(message)
            self._finish_apply()
        if request_id == self._request_seq:
            self._params = self._params_key = None
            self.preview.show_error(message)

    def _show_params(self, key: InputsKey, params: SubcatchmentParameters) -> None:
        self._params, self._params_key = params, key
        self.preview.show_parameters(params)

    def current_parameters(self) -> SubcatchmentParameters | None:
        """Parameters shown in the preview, if they match the current inputs."""
        return self._params if self._params_key == self._inputs_key() else None

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
        enabled = self._engine_ready and has_model and not self._busy
        self.add_button.setEnabled(enabled)
        self.add_action.setEnabled(enabled)
        self.add_button.setText("Adding…" if self._busy else "Add subcatchment")

        if self._status_timer.isActive() and not self._busy:
            return  # a confirmation is being shown; it reverts when the timer fires
        set_prop(self.add_hint, "role", "caption")
        if self._busy:
            hint = "Writing the model…"
        elif self._engine_failed:
            hint = "The fuzzy engine is not available."
        elif not self._engine_ready:
            hint = "Preparing fuzzy engine…"
        elif not has_model:
            hint = "Fix the model path first." if self.path_field.text().strip() else "Choose a SWMM model first."
        else:
            shortcut = self.add_action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
            hint = f"Press {shortcut} to add" if shortcut else ""
        self.add_hint.setText(hint)
        self.add_button.setToolTip(hint if not enabled else "")

    # ------------------------------------------------------------------ add / undo
    def add_subcatchment(self) -> None:
        """Write the subcatchment for the inputs as they are now (later edits do not leak in)."""
        source = self.path_field.path()
        if self._busy or not self._engine_ready or source is None:
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
        ctx = _ApplyContext(source=source, output=output, key=key, to_copy=output is not None)
        self._apply_ctx = ctx
        self._set_busy(True)

        params = self._cache.get(key)
        if params is None and self._params_key == key:
            params = self._params
        if params is not None:
            self._start_apply(params)
        else:
            ctx.request_id = self._issue_request(key, pinned=True)

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
        task = Task(_apply_and_fingerprint, ctx.source, params, ctx.output)
        task.signals.succeeded.connect(self._on_apply_succeeded)
        task.signals.failed.connect(self._on_apply_failed)
        task.signals.finished.connect(self._on_apply_finished)
        self._task = task
        self._pool.start(task)

    def _on_apply_succeeded(self, outcome: tuple[ApplyResult, str | None]) -> None:
        result, digest = outcome
        ctx = self._apply_ctx
        params = ctx.params if ctx is not None else None
        output_path = Path(result.output_path)
        entry = _Entry(
            subcatchment_ids=tuple(result.subcatchment_ids),
            area_ha=params.area_ha if params is not None else float("nan"),
            catchment_type=params.catchment_type if params is not None else "",
            output_path=output_path,
            backup_path=Path(result.backup_path) if result.backup_path is not None else None,
            written_sha256=digest,
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
        if not backup.is_file():
            self.banner.show_error(f"The backup no longer exists: {backup}")
            return False
        expected = getattr(entry, "written_sha256", None)
        if expected is not None and _sha256(target) != expected:
            self.banner.show_error(
                f"{target.name} has changed since RCG wrote it, so it was not restored automatically. "
                f"The backup is still available at {backup}."
            )
            return False
        try:
            restore_backup(backup, target)
        except OSError as exc:
            logger.warning("Undo failed", exc_info=True)
            self.banner.show_error(f"Could not restore {target.name}: {exc.strerror or exc}")
            return False
        entry.undone = True
        self.history.refresh()
        self.path_field.revalidate()
        self.flash_status(f"Undone: {entry.title} removed from {target.name}")
        logger.info("Restored %s from %s", target, backup)
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
            self.path_field.set_path(filename)
            self.path_field.edit.setFocus(Qt.FocusReason.OtherFocusReason)

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
        self.shutdown(wait_ms=CLOSE_WAIT_MS)
        super().closeEvent(event)

    def shutdown(self, wait_ms: int | None = None) -> None:
        """Stop background work, waiting at most *wait_ms* (``None``: until it is done)."""
        self._debounce.stop()
        self._engine_thread.quit()
        if wait_ms is None:
            self._engine_thread.wait()
            self._pool.waitForDone()
        else:
            self._engine_thread.wait(wait_ms)
            self._pool.waitForDone(wait_ms)

    def engine_thread_running(self) -> bool:
        return self._engine_thread.isRunning()


def _stop_thread(thread: QThread, *_: object) -> None:
    try:
        thread.quit()
        thread.wait()
    except RuntimeError:  # already deleted
        pass


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
