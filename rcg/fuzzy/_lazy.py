"""Thread-safe, lazily built shared instances."""

from __future__ import annotations

import functools
import threading
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

__all__ = ["lazy_singleton"]


def lazy_singleton(factory: Callable[[], T]) -> Callable[[], T]:
    """Turn *factory* into a getter that builds its result on first call and then reuses it.

    Concurrent first calls build the instance once (double-checked locking). Use it as
    a decorator; the getter keeps the factory's name and docstring::

        @lazy_singleton
        def get_default_memberships() -> Memberships:
            return Memberships()
    """
    lock = threading.Lock()
    box: list[T] = []

    @functools.wraps(factory)
    def get() -> T:
        if not box:
            with lock:
                if not box:
                    box.append(factory())
        return box[0]

    return get
