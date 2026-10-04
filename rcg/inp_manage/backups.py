"""Backups of SWMM models: created before RCG overwrites a file, restored on undo.

Backups live in ``<dir>/.rcg_backups/`` next to the model, named
``<stem>_backup_<timestamp><suffix>``.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from rcg.exceptions import ModelOperationError

__all__ = ["BACKUP_DIR_NAME", "create_backup"]

BACKUP_DIR_NAME = ".rcg_backups"


def create_backup(path: Path) -> Path:
    """Copy ``path`` to ``<dir>/.rcg_backups/<stem>_backup_<timestamp><suffix>`` and return the copy.

    The name is reserved with an exclusive create, so a backup never replaces another one:
    when the timestamp repeats (the clock on Windows is coarse), ``_1``, ``_2``, ... is appended.
    """
    backup_dir = path.parent / BACKUP_DIR_NAME
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    try:
        backup_dir.mkdir(exist_ok=True)
        target = _reserve_backup_name(backup_dir, f"{path.stem}_backup_{stamp}", path.suffix)
        shutil.copy2(path, target)
    except OSError as e:
        raise ModelOperationError(
            f"Cannot create backup in {backup_dir}: {e}", operation="backup", model_path=str(path)
        ) from e
    return target


def _reserve_backup_name(directory: Path, base: str, suffix: str) -> Path:
    """Create an empty, previously non-existent ``<base>[_n]<suffix>`` in *directory* and return it."""
    for n in range(10_000):
        candidate = directory / (f"{base}{suffix}" if n == 0 else f"{base}_{n}{suffix}")
        try:
            with open(candidate, "xb"):
                return candidate
        except FileExistsError:
            continue
    raise FileExistsError(f"No free backup name for {base}{suffix} in {directory}")
