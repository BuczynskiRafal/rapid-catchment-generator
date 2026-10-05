import threading
import time

from rcg.fuzzy._lazy import lazy_singleton


def test_builds_once_and_reuses():
    calls = []

    @lazy_singleton
    def get() -> object:
        """Docstring is kept."""
        calls.append(1)
        return object()

    assert get() is get()
    assert calls == [1]
    assert get.__doc__ == "Docstring is kept."
    assert get.__name__ == "get"


def test_concurrent_first_calls_build_once():
    calls = []
    start = threading.Barrier(8)

    @lazy_singleton
    def get() -> object:
        calls.append(1)
        time.sleep(0.05)  # widen the race window
        return object()

    results = []

    def worker() -> None:
        start.wait()
        results.append(get())

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert calls == [1]
    assert len({id(r) for r in results}) == 1


def test_failed_build_is_retried():
    attempts = []

    @lazy_singleton
    def get() -> str:
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError("first build fails")
        return "ok"

    try:
        get()
    except RuntimeError:
        pass
    assert get() == "ok"
    assert len(attempts) == 2
