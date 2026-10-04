"""The single RCG window.

Layout, top to bottom: the header; the SWMM model across the full width; the inputs
(with the primary action) and the live preview side by side, always of equal height;
the session history across the full width, which takes whatever height is left.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QSettings, QSize, Qt, QThreadPool
from PySide6.QtGui import (
    QCloseEvent,
    QShowEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from rcg.exceptions import RCGError
from rcg.gui.cards import OUTPUT_COPY, OUTPUT_IN_PLACE, InputsCard, ModelCard, align_field_labels
from rcg.gui.file_actions import ask_save_path, choose_output_path, confirm_replace, normalise_output_path, show_in_folder
from rcg.gui.help_dialog import HelpDialog, show_about_box
from rcg.gui.menus import install_menus, shortcut_text
from rcg.gui.preview_controller import InputsKey, PreviewController
from rcg.gui.widgets import HistoryEntry, HistoryPanel, MessageBanner, PreviewPanel
from rcg.gui.widgets._util import hbox, vbox
from rcg.gui.widgets.containers import VerticalScrollArea, WindowCentral, invalidate_layouts
from rcg.gui.widgets.drop import FileDropFilter
from rcg.gui.widgets.header import build_header
from rcg.gui.widgets.preview import PREPARING_TEXT
from rcg.gui.workers import Task
from rcg.logging_config import get_logger

if TYPE_CHECKING:
    from rcg.catchment import ApplyResult, ModelInfo, SubcatchmentParameters
    from rcg.fuzzy.engine import FuzzyEngine

__all__ = ["MainWindow", "OUTPUT_COPY", "OUTPUT_IN_PLACE", "normalise_output_path"]

logger = get_logger("gui")  # one logger for the whole GUI (rcg.gui)

APP_TITLE = "Rapid Catchment Generator"
SUBTITLE = "SWMM subcatchments from land form and land cover"
ENGINE_FAILED_TEXT = "The fuzzy engine could not be started."
PREVIEW_FAILED_TEXT = "The preview could not be computed."
CLOSE_WAIT_MS = 200

_KEY_GEOMETRY = "window/geometry"
_KEY_LAST_DIR = "paths/last_dir"
_KEY_OUTPUT_MODE = "output/mode"


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

        self._settings = settings if settings is not None else QSettings()
        self._log_path = log_path
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

    def _build_ui(self) -> None:
        central = WindowCentral(self)
        central.setObjectName("central")
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 18)
        root.setSpacing(self.GAP)

        header, self.help_button = build_header(central, APP_TITLE, SUBTITLE)
        self.help_button.clicked.connect(self.show_help)
        root.addLayout(header)
        self.banner = MessageBanner(central)
        root.addWidget(self.banner)
        root.addWidget(self._build_workspace(central))

        self.history = HistoryPanel(central)
        self.history.undoRequested.connect(self.undo_entry)
        self.history.showInFolderRequested.connect(self._show_in_folder)
        root.addWidget(self.history, 1)  # the only part that grows with the window

        self.setCentralWidget(central)
        align_field_labels([*self.model_card.field_labels, *self.inputs_card.field_labels])
        self._set_tab_order()

    def _build_workspace(self, parent: QWidget) -> QScrollArea:
        """Model across the top; inputs and preview below it, side by side and level.

        The model comes first: it gates everything else, and its Output choice must stay
        in view. The inputs card stretches to the preview's height and pins the primary
        action to its bottom, so both cards end on the same line.
        """
        content = QWidget()
        content.setObjectName("inputsContent")

        self.preview = PreviewPanel(content)
        self.inputs_card = InputsCard(content)
        self.model_card = ModelCard(content)
        self._adopt_card_widgets()
        row = hbox((self.inputs_card, 1), (self.preview, 1), spacing=self.GAP)
        vbox(self.model_card, row, spacing=self.GAP, parent=content)

        self.inputs_scroll = VerticalScrollArea(parent)
        self.inputs_scroll.setObjectName("inputsScroll")
        self.inputs_scroll.setWidgetResizable(True)
        self.inputs_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.inputs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.inputs_scroll.setWidget(content)
        self.inputs_scroll.viewport().setAutoFillBackground(False)
        content.setAutoFillBackground(False)
        return self.inputs_scroll

    def _adopt_card_widgets(self) -> None:
        """Expose the cards' widgets on the window (tests and the window's own code use them)."""
        model, inputs = self.model_card, self.inputs_card
        self.path_field = model.path_field
        self.in_place_radio, self.copy_radio, self.output_group = model.in_place_radio, model.copy_radio, model.output_group
        self.cover_combo, self.form_combo, self.area_spin = inputs.cover_combo, inputs.form_combo, inputs.area_spin
        self.cover_hint, self.form_hint = inputs.cover_hint, inputs.form_hint
        self.add_hint, self.add_button = inputs.add_hint, inputs.add_button

        self.path_field.modelChanged.connect(self._on_model_changed)
        self._drop_filter = FileDropFilter(self, dropped=self.open_model, highlight=self.path_field.set_drop_highlight)
        self.output_group.buttonToggled.connect(self._on_output_mode_changed)
        inputs.inputsChanged.connect(self._schedule_preview)
        inputs.statusExpired.connect(self._update_add_state)
        self.add_button.clicked.connect(self.add_subcatchment)

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
        actions = install_menus(
            self,
            open_model=self.path_field.browse,
            add=self.add_subcatchment,
            show_help=self.show_help,
            show_about=self.show_about,
        )
        self.open_action, self.add_action, self.help_action = actions.open, actions.add, actions.help
        open_hint = shortcut_text(self.open_action)
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
        return self.inputs_card.inputs_key()

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
    def _on_model_changed(self, info: ModelInfo | None) -> None:
        path = info.path if info is not None else None
        if path != self._model_path:
            self._model_path = path
            self.inputs_card.clear_status()  # a stale "Added ..." confirmation would be misleading now
            if path is not None:
                self._remember_directory(path)
        self.preview.set_model(info)
        self._update_add_state()

    def _on_output_mode_changed(self) -> None:
        if not self._switching_mode:  # only the user's own choice is remembered
            self._preferred_mode = self.output_mode()
            self._settings.setValue(_KEY_OUTPUT_MODE, self._preferred_mode)

    def output_mode(self) -> str:
        return self.model_card.output_mode()

    def _update_add_state(self) -> None:
        has_model = self.path_field.path() is not None
        enabled = self.preview_controller.ready and has_model and not self._busy
        self.add_action.setEnabled(enabled)
        self.inputs_card.show_add_state(enabled=enabled, busy=self._busy, hint=self._add_hint(has_model))

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
        shortcut = shortcut_text(self.add_action)
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
        return choose_output_path(source, ask=self._ask_save_path, confirm=self._confirm_replace)

    def _ask_save_path(self, suggestion: Path) -> str | None:
        """Run the save dialog (separate method so tests can replace it)."""
        return ask_save_path(self, suggestion)

    def _confirm_replace(self, path: Path) -> bool:
        """Ask before overwriting a file the save dialog did not confirm."""
        return confirm_replace(self, path)

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
            self.inputs_card.clear_status()  # the previous confirmation no longer applies
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
        self.inputs_card.flash_status(text, timeout_ms)

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
        show_about_box(self, APP_TITLE)

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
            invalidate_layouts(central_layout)
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
