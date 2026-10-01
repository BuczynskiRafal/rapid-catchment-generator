"""Background execution for the slow calls.

* :class:`EngineWorker` owns the fuzzy engine on one dedicated ``QThread``. It warms the
  engine up (several seconds) and then serves :func:`rcg.service.preview` requests
  (~0.1 s each). The skfuzzy simulations are stateful, so the engine is only ever used
  from that single thread.
* :class:`Task` runs one callable on a :class:`~PySide6.QtCore.QThreadPool` (used for
  :func:`rcg.service.apply`, which does not touch the engine).

Results come back through Qt signals and are delivered on the GUI thread.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

if TYPE_CHECKING:
    from rcg.fuzzy.categories import LandCover, LandForm
    from rcg.fuzzy.engine import FuzzyEngine

__all__ = ["EngineWorker", "Task", "TaskSignals"]


def _emit(signal: Any, *args: Any) -> None:
    """Emit *signal*, unless its object has been deleted meanwhile.

    That only happens when the process shuts down while the worker is still busy; there
    is nobody left to receive the result then.
    """
    try:
        signal.emit(*args)
    except RuntimeError as exc:
        if "deleted" not in str(exc):
            raise


class TaskSignals(QObject):
    """Signals emitted by :class:`Task`; ``failed`` carries the exception instance."""

    succeeded = Signal(object)
    failed = Signal(object)
    finished = Signal()


class Task(QRunnable):
    """Run ``fn(*args, **kwargs)`` off the GUI thread; keep a reference until ``finished``."""

    def __init__(self, fn: Callable[..., Any], /, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        # The pool must not delete the C++ object: Python owns the task.
        self.setAutoDelete(False)
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.signals = TaskSignals()

    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # reported to the GUI, which decides how to surface it
            self.signals.failed.emit(exc)
        else:
            self.signals.succeeded.emit(result)
        finally:
            self.signals.finished.emit()


class EngineWorker(QObject):
    """Lives on a dedicated thread; builds the engine and computes previews serially.

    Requests carry an increasing id. Requests superseded by a newer one before they
    start are skipped, so fast typing never builds up a queue of stale computations.
    A *pinned* request (the inputs an Add was clicked with) is always computed.

    :mod:`rcg.service` is imported here, on the worker thread, when the work starts:
    building the engine is what loads skfuzzy, and that never happens on the GUI thread.
    """

    ready = Signal()
    warmUpFailed = Signal(object)  # exception
    previewReady = Signal(int, object)  # request id, SubcatchmentParameters
    previewFailed = Signal(int, object)  # request id, exception

    def __init__(self, engine: FuzzyEngine | None = None) -> None:
        super().__init__()
        self._engine: FuzzyEngine | None = engine
        self._latest_lock = threading.Lock()
        self._latest_id = 0

    def note_request(self, request_id: int) -> None:
        """Record (from the GUI thread) the id of the newest request."""
        with self._latest_lock:
            self._latest_id = max(self._latest_id, request_id)

    def _is_stale(self, request_id: int) -> bool:
        with self._latest_lock:
            return request_id < self._latest_id

    @Slot()
    def warm_up(self) -> None:
        try:
            from rcg import service

            self._engine = service.warm_up(self._engine)
        except Exception as exc:
            _emit(self.warmUpFailed, exc)
        else:
            _emit(self.ready)

    @Slot(int, object, bool)
    def compute(self, request_id: int, request: tuple[float, LandForm, LandCover], pinned: bool = False) -> None:
        if self._engine is None or (not pinned and self._is_stale(request_id)):
            return
        area_ha, land_form, land_cover = request
        try:
            from rcg import service

            params = service.preview(area_ha, land_form, land_cover, engine=self._engine)
        except Exception as exc:
            _emit(self.previewFailed, request_id, exc)
        else:
            _emit(self.previewReady, request_id, params)
