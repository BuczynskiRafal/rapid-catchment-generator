"""Live preview: the fuzzy engine thread, request bookkeeping, cache and debounce.

:class:`PreviewController` turns the window's inputs into
:class:`~rcg.catchment.SubcatchmentParameters`. It owns the :class:`~rcg.gui.workers.EngineWorker`
and its ``QThread``, so the window only connects to a handful of signals:

* ``previewReady(key, params)`` / ``previewFailed(exc)`` for the inputs currently shown;
* ``pinnedReady(id, params)`` / ``pinnedFailed(id, exc)`` for a request made by :meth:`pin`
  (the inputs an Add was clicked with), which is computed even when newer inputs follow;
* ``engineReady()`` / ``engineFailed(exc)`` once the warm-up ends.

Each request gets an increasing id. A newer id makes older, unpinned requests stale: the
worker skips them if they have not started, and their results are only cached, never
shown. Results are cached per inputs (up to ``_CACHE_LIMIT`` entries), so going back to
earlier inputs shows the preview without recomputing it.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from rcg.exceptions import RCGError
from rcg.gui.workers import EngineWorker
from rcg.logging_config import get_logger

if TYPE_CHECKING:
    from rcg.catchment import SubcatchmentParameters
    from rcg.fuzzy.categories import LandCover, LandForm
    from rcg.fuzzy.engine import FuzzyEngine

__all__ = ["InputsKey", "PREVIEW_DEBOUNCE_MS", "PreviewController"]

logger = get_logger("gui")

PREVIEW_DEBOUNCE_MS = 150
_CACHE_LIMIT = 512

InputsKey = tuple[float, "LandForm", "LandCover"]  # (area_ha rounded to 2 dp, land form, land cover)


class PreviewController(QObject):
    """Compute previews on the engine thread for the inputs returned by *inputs*.

    Parameters
    ----------
    inputs : callable
        Returns the current :data:`InputsKey`; called whenever a preview is requested.
    engine : FuzzyEngine, optional
        A pre-built engine (tests share one). It is still warmed up on the engine thread.
    parent : QObject, optional
        Owner; the engine thread is stopped before the controller is destroyed.
    """

    engineReady = Signal()
    engineFailed = Signal(object)  # exception
    previewReady = Signal(object, object)  # InputsKey, SubcatchmentParameters
    previewFailed = Signal(object)  # exception
    pinnedReady = Signal(int, object)  # request id, SubcatchmentParameters
    pinnedFailed = Signal(int, object)  # request id, exception
    _requested = Signal(int, object, bool)  # request id, InputsKey, pinned

    def __init__(
        self, inputs: Callable[[], InputsKey], *, engine: FuzzyEngine | None = None, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._inputs = inputs
        self._ready = False
        self._failed = False
        self._closed = False
        self._request_seq = 0
        self._requests: dict[int, InputsKey] = {}
        self._pinned: int | None = None
        self._cache: dict[InputsKey, SubcatchmentParameters] = {}
        self._shown: tuple[InputsKey, SubcatchmentParameters] | None = None

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(PREVIEW_DEBOUNCE_MS)
        self._debounce.timeout.connect(self.request)

        self._thread = QThread(self)
        self._thread.setObjectName("rcg-fuzzy-engine")
        self._worker = EngineWorker(engine)
        self._worker.moveToThread(self._thread)
        self._worker.ready.connect(self._on_ready)
        self._worker.warmUpFailed.connect(self._on_warm_up_failed)
        self._worker.previewReady.connect(self._on_computed)
        self._worker.previewFailed.connect(self._on_failed)
        self._requested.connect(self._worker.compute)
        self._thread.started.connect(self._worker.warm_up)
        # No `finished -> deleteLater`: the worker is owned by Python (this controller), and
        # deleting its wrapper from the worker thread segfaults in shiboken. It is freed
        # with the controller, on the GUI thread, after the thread has stopped.
        # If the controller is destroyed without being shut down (e.g. its window is
        # garbage-collected), stop the thread before Qt deletes it: `destroyed` fires
        # before children are deleted.
        self.destroyed.connect(partial(_stop_thread, self._thread))
        # (A child timer, not QTimer.singleShot: it dies with the controller, so it can
        # never start the thread of a window that is already gone.)
        self._start_timer = QTimer(self)
        self._start_timer.setSingleShot(True)
        self._start_timer.timeout.connect(self._start_thread)

    # -- lifecycle -------------------------------------------------------------------
    def start(self) -> None:
        """Start the engine thread from the event loop, so the window paints first.

        Nothing heavy (the fuzzy engine, skfuzzy) is imported before the worker thread runs.
        """
        self._start_timer.start(0)

    def _start_thread(self) -> None:
        if not self._closed:
            self._thread.start()

    def close(self) -> None:
        """Ignore a warm-up that finishes from now on, and never start the thread."""
        self._closed = True

    def shutdown(self, wait_ms: int | None = None) -> None:
        """Stop the engine thread, waiting at most *wait_ms* (``None``: until it is done)."""
        self._debounce.stop()
        self._thread.quit()
        if wait_ms is None:
            self._thread.wait()
        else:
            self._thread.wait(wait_ms)

    def thread_running(self) -> bool:
        return self._thread.isRunning()

    @property
    def ready(self) -> bool:
        """The engine is warmed up and previews can be computed."""
        return self._ready

    @property
    def failed(self) -> bool:
        """The engine could not be started; no preview will ever be computed."""
        return self._failed

    def _on_ready(self) -> None:
        if self._closed:
            return
        self._ready = True
        logger.info("Fuzzy engine ready")
        self.engineReady.emit()
        self.request()

    def _on_warm_up_failed(self, exc: BaseException) -> None:
        self._failed = True
        _log_unexpected("Fuzzy engine warm-up failed", exc)
        self.engineFailed.emit(exc)

    # -- requests --------------------------------------------------------------------
    def schedule(self) -> None:
        """Request a preview once the inputs have stopped changing for a moment."""
        self._debounce.start()

    def request(self) -> None:
        """Show the preview for the current inputs (cached, or computed on the engine thread)."""
        self._debounce.stop()
        if not self._ready:
            return
        key = self._inputs()
        cached = self._cache.get(key)
        if cached is not None:
            self._supersede()  # results still in flight are now outdated
            self._show(key, cached)
            return
        self._issue(key, pinned=False)

    def pin(self, key: InputsKey) -> int:
        """Compute *key* even if newer inputs follow; the result comes with ``pinned*`` signals.

        Returns the request id those signals carry.
        """
        self._pinned = self._issue(key, pinned=True)
        return self._pinned

    def lookup(self, key: InputsKey) -> SubcatchmentParameters | None:
        """Parameters already known for *key* (cached or shown), without computing them."""
        cached = self._cache.get(key)
        return cached if cached is not None else self.parameters_for(key)

    def parameters_for(self, key: InputsKey) -> SubcatchmentParameters | None:
        """The parameters on show, if they were computed for *key*."""
        return self._shown[1] if self._shown is not None and self._shown[0] == key else None

    def _supersede(self) -> int:
        """Start a new request id; unpinned requests still queued on the engine thread become stale."""
        self._request_seq += 1
        self._worker.note_request(self._request_seq)
        return self._request_seq

    def _issue(self, key: InputsKey, *, pinned: bool) -> int:
        """Send *key* to the engine thread; a *pinned* request is never skipped as stale."""
        request_id = self._supersede()
        # Keep the previous request (its result is still worth caching) and the pinned one.
        keep = {request_id - 1, self._pinned}
        self._requests = {rid: k for rid, k in self._requests.items() if rid in keep}
        self._requests[request_id] = key
        self._requested.emit(request_id, key, pinned)
        return request_id

    # -- results ---------------------------------------------------------------------
    def _remember(self, key: InputsKey, params: SubcatchmentParameters) -> None:
        if key not in self._cache and len(self._cache) >= _CACHE_LIMIT:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = params

    def _show(self, key: InputsKey, params: SubcatchmentParameters) -> None:
        self._shown = (key, params)
        self.previewReady.emit(key, params)

    def _take_pinned(self, request_id: int) -> bool:
        if request_id != self._pinned:
            return False
        self._pinned = None
        return True

    def _on_computed(self, request_id: int, params: SubcatchmentParameters) -> None:
        key = self._requests.pop(request_id, None)
        if key is None:
            return
        self._remember(key, params)
        if self._take_pinned(request_id):
            self.pinnedReady.emit(request_id, params)
        if request_id == self._request_seq:
            self._show(key, params)

    def _on_failed(self, request_id: int, exc: BaseException) -> None:
        if self._requests.pop(request_id, None) is None:
            return
        if not isinstance(exc, RCGError):
            _log_unexpected("Preview failed", exc)
        if self._take_pinned(request_id):
            self.pinnedFailed.emit(request_id, exc)
        if request_id == self._request_seq:
            self._shown = None
            self.previewFailed.emit(exc)


def _log_unexpected(message: str, exc: BaseException) -> None:
    logger.error(message, exc_info=(type(exc), exc, exc.__traceback__))


def _stop_thread(thread: QThread, *_: object) -> None:
    try:
        thread.quit()
        thread.wait()
    except RuntimeError:  # already deleted
        pass
