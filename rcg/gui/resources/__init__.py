"""Static resources of the desktop GUI (icon, help text).

Resources are located with :mod:`importlib.resources` so they work from a source
checkout, an installed wheel and a zipped install alike. Inside a PyInstaller bundle
the data files live under ``sys._MEIPASS``; that location is tried as a fallback.
"""

from __future__ import annotations

import sys
from importlib import resources
from pathlib import Path

__all__ = ["resource_path", "read_text"]

_PACKAGE = __name__  # "rcg.gui.resources"
_BUNDLE_SUBDIR = Path("rcg", "gui", "resources")


def resource_path(name: str) -> Path | None:
    """Return a filesystem path to resource *name*, or ``None`` when it is missing."""
    try:
        candidate = resources.files(_PACKAGE).joinpath(name)
        if candidate.is_file():
            return Path(str(candidate))
    except (ModuleNotFoundError, FileNotFoundError, NotADirectoryError):
        pass
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        bundled = Path(bundle_root) / _BUNDLE_SUBDIR / name
        if bundled.is_file():
            return bundled
    return None


def read_text(name: str, encoding: str = "utf-8") -> str:
    """Return the text of resource *name*; raises ``FileNotFoundError`` if it is missing."""
    path = resource_path(name)
    if path is None:
        raise FileNotFoundError(f"GUI resource not found: {name}")
    return path.read_text(encoding=encoding)
