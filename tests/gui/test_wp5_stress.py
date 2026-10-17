"""Empirical stress and adversarial tests for WP5.

Covers:
1. Task.run() and _emit() in rcg.gui.workers:
   - C++ QObject deletion simulation (real shiboken6.delete and mock signals).
   - Concurrency stress with 60+ parallel Task threads mixing success and failures.
2. ModelPathField debounce timing in rcg.gui.widgets.path_field:
   - Burst typing: 20 updates in 100 ms runs validation at most once after 200 ms.
   - Immediate cancellation and validation on programmatic set_path() and revalidate().
3. Asynchronous undo stress in MainWindow:
   - Rapid consecutive undo requests while restore task is in flight.
   - UI busy state (_set_busy) disabling conflicting actions (add_subcatchment, undo).
   - Error resilience: failure properly resets busy state and shows error banner.
   - Window closure while undo task is in flight.
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest
import shiboken6
from gui_helpers import add_and_wait
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication

from rcg.exceptions import RCGError
from rcg.gui.main_window import MainWindow
from rcg.gui.widgets.path_field import ModelPathField
from rcg.gui.workers import Task, _emit

# ==============================================================================
# 1. Task.run() and _emit() C++ deletion and concurrency stress
# ==============================================================================


def test_emit_swallows_deleted_qobject_runtime_errors():
    """_emit() catches and swallows any RuntimeError containing 'deleted'."""
    deleted_messages = [
        "Signal source has been deleted",
        "wrapped C/C++ object of type TaskSignals has been deleted",
        "Internal C++ object (TaskSignals) already deleted.",
        "Object has been deleted meanwhile",
    ]
    for msg in deleted_messages:
        mock_signal = MagicMock()
        mock_signal.emit.side_effect = RuntimeError(msg)
        # Should not raise
        _emit(mock_signal, "arg1", 123)


def test_emit_propagates_unrelated_runtime_errors():
    """_emit() re-raises RuntimeErrors that are not related to deleted objects."""
    mock_signal = MagicMock()
    mock_signal.emit.side_effect = RuntimeError("Resource temporarily unavailable")
    with pytest.raises(RuntimeError, match="Resource temporarily unavailable"):
        _emit(mock_signal, "data")


def test_task_run_resilient_to_underlying_qobject_deletion_success():
    """Task.run() handles C++ deletion of task.signals cleanly on success path."""
    task = Task(lambda: "computed_value")
    shiboken6.delete(task.signals)
    # Underlying QObject is deleted; run() must complete cleanly without crash or unhandled error
    task.run()


def test_task_run_resilient_to_underlying_qobject_deletion_failure():
    """Task.run() handles C++ deletion of task.signals cleanly on failure path."""

    def fail():
        raise ValueError("simulated background failure")

    task = Task(fail)
    shiboken6.delete(task.signals)
    task.run()


def test_task_run_signals_deleted_concurrently_during_execution(qtbot):
    """Task.run() handles C++ deletion of task.signals while task function is executing in thread."""
    pool = QThreadPool()
    entered_fn = threading.Event()
    continue_fn = threading.Event()

    def worker_func():
        entered_fn.set()
        continue_fn.wait(timeout=2.0)
        return "mid_flight_result"

    task = Task(worker_func)
    pool.start(task)

    # Wait until worker function is actively running
    assert entered_fn.wait(timeout=2.0)

    # Delete signals while thread is blocked inside worker_func
    shiboken6.delete(task.signals)

    # Allow worker function to complete and attempt signal emissions
    continue_fn.set()

    def check_done():
        return pool.activeThreadCount() == 0

    qtbot.waitUntil(check_done, timeout=3000)
    pool.waitForDone(1000)


def test_task_run_concurrency_stress(qtbot):
    """Stress test running 64 concurrent Task threads simultaneously."""
    pool = QThreadPool()
    pool.setMaxThreadCount(64)

    total_tasks = 64
    success_count = 0
    failure_count = 0
    finished_count = 0
    lock = threading.Lock()

    def make_task(i: int):
        if i % 3 == 0:
            # Failing task
            def fail_fn(idx=i):
                time.sleep(0.01)
                raise ValueError(f"stress_error_{idx}")

            t = Task(fail_fn)
        else:
            # Successful task
            def success_fn(idx=i):
                time.sleep(0.01)
                return sum(range(idx * 50))

            t = Task(success_fn)

        def on_success(_result):
            nonlocal success_count
            with lock:
                success_count += 1

        def on_failed(_exc):
            nonlocal failure_count
            with lock:
                failure_count += 1

        def on_finished():
            nonlocal finished_count
            with lock:
                finished_count += 1

        t.signals.succeeded.connect(on_success)
        t.signals.failed.connect(on_failed)
        t.signals.finished.connect(on_finished)
        return t

    tasks = [make_task(i) for i in range(total_tasks)]
    expected_failures = sum(1 for i in range(total_tasks) if i % 3 == 0)
    expected_successes = total_tasks - expected_failures

    for t in tasks:
        pool.start(t)

    qtbot.waitUntil(lambda: finished_count == total_tasks, timeout=10_000)

    assert finished_count == total_tasks
    assert success_count == expected_successes
    assert failure_count == expected_failures
    pool.waitForDone(5000)


# ==============================================================================
# 2. ModelPathField debounce timing and programmatic assignment
# ==============================================================================


def test_model_path_field_rapid_typing_debounces_single_validation(qtbot):
    """Rapid simulated typing (20 updates in 100 ms) executes validation at most once after 200 ms."""
    field = ModelPathField()
    qtbot.addWidget(field)

    revalidate_calls: list[str] = []
    orig_revalidate = field._revalidate

    def spy_revalidate(text: str) -> None:
        revalidate_calls.append(text)
        orig_revalidate(text)

    field._revalidate = spy_revalidate  # type: ignore[method-assign]

    # Simulate 20 rapid keystrokes within 100 ms (5ms intervals)
    for i in range(20):
        field.edit.setText(f"nonexistent_model_{i}.inp")
        QApplication.processEvents()
        time.sleep(0.005)

    # During the 100 ms typing burst, debounce timer was repeatedly restarted; no revalidation yet
    assert len(revalidate_calls) == 0
    assert field._debounce.isActive()

    # Wait for the 200 ms debounce timer to fire
    qtbot.waitUntil(lambda: len(revalidate_calls) == 1, timeout=1000)
    assert not field._debounce.isActive()
    assert revalidate_calls == ["nonexistent_model_19.inp"]


def test_model_path_field_debounce_rearm_extends_delay(qtbot):
    """Typing again at 120 ms resets the 200 ms debounce window."""
    field = ModelPathField()
    qtbot.addWidget(field)

    revalidate_calls: list[str] = []
    orig_revalidate = field._revalidate

    def spy_revalidate(text: str) -> None:
        revalidate_calls.append(text)
        orig_revalidate(text)

    field._revalidate = spy_revalidate  # type: ignore[method-assign]

    # Keystroke 1 at t=0
    field.edit.setText("step1")
    assert field._debounce.isActive()

    # Wait 120 ms (less than 200 ms timeout)
    qtbot.wait(120)
    assert len(revalidate_calls) == 0

    # Keystroke 2 at t=120 ms (re-arms timer for 200 ms from now)
    field.edit.setText("step2")
    assert field._debounce.isActive()

    # Wait another 120 ms (total 240 ms from step1, but only 120 ms from step2)
    qtbot.wait(120)
    # Should STILL have not fired!
    assert len(revalidate_calls) == 0
    assert field._debounce.isActive()

    # Wait another 120 ms (total 240 ms from step2) -> now it must have fired
    qtbot.waitUntil(lambda: len(revalidate_calls) == 1, timeout=1000)
    assert revalidate_calls == ["step2"]


def test_model_path_field_programmatic_assignment_immediate(qtbot, model_copy):
    """set_path() and revalidate() immediately cancel debounce timer and validate synchronously."""
    field = ModelPathField()
    qtbot.addWidget(field)

    # 1. Type text to trigger debounce timer
    field.edit.setText("some_typed_path.inp")
    assert field._debounce.isActive()

    # 2. Programmatic set_path must stop debounce timer and inspect model immediately
    field.set_path(model_copy)
    assert not field._debounce.isActive()
    assert field.path() == model_copy.resolve()
    info = field.model_info()
    assert info is not None
    assert info.subcatchment_count == 15

    # 3. Another typed input re-arms debounce
    field.edit.setText("another_path.inp")
    assert field._debounce.isActive()

    # 4. Explicit revalidate() must stop debounce and run immediately
    field.revalidate()
    assert not field._debounce.isActive()


# ==============================================================================
# 3. Asynchronous Undo and Busy State Stress
# ==============================================================================


def test_async_undo_rapid_consecutive_triggers_and_busy_state(qtbot, window, model_copy, monkeypatch):
    """Rapid consecutive undo triggers reject secondary calls and busy state prevents conflicting actions."""
    from rcg import service

    window.path_field.set_path(model_copy)
    add_and_wait(qtbot, window)
    assert len(window.history.entries) == 1

    entry = window.history.undo_candidate()
    assert entry is not None

    # Inject artificial delay into service.restore to hold task in flight
    original_restore = service.restore

    def slow_restore(*args, **kwargs):
        time.sleep(0.15)
        return original_restore(*args, **kwargs)

    monkeypatch.setattr(service, "restore", slow_restore)

    # 1. First trigger should succeed and set busy state
    started = window.undo_entry(entry)
    assert started is True
    assert window.busy is True
    assert not window.add_button.isEnabled()
    assert not window.add_action.isEnabled()

    # 2. Rapid subsequent undo calls while in-flight must be rejected
    for _ in range(5):
        assert window.undo_entry(entry) is False

    # 3. add_subcatchment must be blocked while busy
    initial_entries_count = len(window.history.entries)
    window.add_subcatchment()
    assert len(window.history.entries) == initial_entries_count

    # 4. Wait for in-flight restore to complete
    qtbot.waitUntil(lambda: not window.busy, timeout=5000)
    assert window.busy is False
    assert entry.undone is True
    assert window.history.undo_candidate() is None

    # 5. Subsequent undo calls on already undone entry must return False
    assert window.undo_entry(entry) is False


def test_async_undo_failure_recovers_busy_state(qtbot, window, model_copy, monkeypatch):
    """If asynchronous undo fails, busy state is cleanly reset and error banner is displayed."""
    from rcg import service

    window.path_field.set_path(model_copy)
    add_and_wait(qtbot, window)
    entry = window.history.undo_candidate()
    assert entry is not None

    # Simulate restore failure (e.g. hash mismatch or file corruption)
    def failing_restore(*args, **kwargs):
        time.sleep(0.05)
        raise RCGError("Simulated backup checksum mismatch")

    monkeypatch.setattr(service, "restore", failing_restore)

    started = window.undo_entry(entry)
    assert started is True
    assert window.busy is True

    # Secondary undo calls while in flight are still rejected
    assert window.undo_entry(entry) is False

    # Wait for failure handler
    qtbot.waitUntil(lambda: not window.busy, timeout=5000)
    assert window.busy is False
    assert entry.undone is False  # entry was NOT successfully undone
    assert "Simulated backup checksum mismatch" in window.banner.text


def test_window_closure_during_in_flight_undo(qtbot, gui_settings, gui_engine, model_copy, monkeypatch):
    """Closing MainWindow while an asynchronous undo Task is in flight does not crash."""
    from rcg import service

    win = MainWindow(gui_settings, engine=gui_engine)
    qtbot.addWidget(win)
    win.show()
    qtbot.waitUntil(lambda: win.engine_ready, timeout=10_000)

    win.path_field.set_path(model_copy)
    add_and_wait(qtbot, win)
    entry = win.history.undo_candidate()
    assert entry is not None

    restore_started = threading.Event()
    original_restore = service.restore

    def slow_restore(*args, **kwargs):
        restore_started.set()
        time.sleep(0.1)
        return original_restore(*args, **kwargs)

    monkeypatch.setattr(service, "restore", slow_restore)

    win.undo_entry(entry)
    assert win.busy is True
    restore_started.wait(timeout=2.0)

    # Close window while thread is still executing
    win.close()
    qtbot.waitUntil(lambda: win._pool.activeThreadCount() == 0, timeout=3000)
    QApplication.processEvents()


def test_async_undo_multiple_entries_sequential_stress(qtbot, window, model_copy, monkeypatch):
    """Multiple history entries: undo candidate enforcement and sequential undo under async flight."""
    from rcg import service

    window.path_field.set_path(model_copy)
    # Add two subcatchments
    add_and_wait(qtbot, window)
    add_and_wait(qtbot, window)
    assert len(window.history.entries) == 2

    # entry_newest is entries[0], entry_older is entries[1]
    entry_newest = window.history.entries[0]
    entry_older = window.history.entries[1]
    assert window.history.undo_candidate() is entry_newest

    # 1. Attempting to undo the older entry before the newest is rejected
    assert window.undo_entry(entry_older) is False

    # 2. Start undo on the newest entry with simulated delay
    original_restore = service.restore

    def slow_restore(*args, **kwargs):
        time.sleep(0.1)
        return original_restore(*args, **kwargs)

    monkeypatch.setattr(service, "restore", slow_restore)

    assert window.undo_entry(entry_newest) is True
    assert window.busy is True

    # 3. Both newest and older undos are rejected while in flight
    assert window.undo_entry(entry_newest) is False
    assert window.undo_entry(entry_older) is False

    # 4. Wait for newest undo to complete
    qtbot.waitUntil(lambda: not window.busy, timeout=5000)
    assert entry_newest.undone is True

    # 5. Now older entry becomes the active candidate
    assert window.history.undo_candidate() is entry_older

    # 6. Undo older entry
    assert window.undo_entry(entry_older) is True
    qtbot.waitUntil(lambda: not window.busy, timeout=5000)
    assert entry_older.undone is True
    assert window.history.undo_candidate() is None
