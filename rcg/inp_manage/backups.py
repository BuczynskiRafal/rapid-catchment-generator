"""Backups of SWMM models: created before RCG overwrites a file, restored on undo.

Backups live in ``<dir>/.rcg_backups/`` next to the model, named
``<stem>_backup_<timestamp><suffix>``.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from rcg.exceptions import BackupError, ModelOperationError

__all__ = ["BACKUP_DIR_NAME", "create_backup", "file_sha256", "restore_backup"]

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


def file_sha256(path: Path) -> str | None:
    """Return the hex SHA-256 of the file at *path*, or ``None`` when it cannot be read."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def restore_backup(backup: Path, target: Path, *, expected_sha256: str | None = None) -> None:
    """Copy *backup* back over *target* atomically; the backup is kept.

    Parameters
    ----------
    backup : Path
        Backup made by :func:`create_backup`.
    target : Path
        File to restore.
    expected_sha256 : str, optional
        Hex SHA-256 of *target* as RCG wrote it (:attr:`rcg.ApplyResult.written_sha256`).
        When given and *target* no longer matches (edited, replaced or deleted since),
        nothing is restored, so changes made elsewhere are never thrown away.

    Raises
    ------
    BackupError
        If the backup no longer exists, *target* changed since it was written, or the
        copy fails. *target* is never left half-written.
    """
    backup, target = Path(backup), Path(target)
    if not backup.is_file():
        raise BackupError(f"The backup no longer exists: {backup}", backup_path=str(backup))
    if expected_sha256 is not None and file_sha256(target) != expected_sha256:
        raise BackupError(
            f"{target.name} has changed since RCG wrote it, so it was not restored automatically. "
            f"The backup is still available at {backup}.",
            backup_path=str(backup),
        )
    try:
        fd, tmp_name = tempfile.mkstemp(prefix=f".{target.stem}.", suffix=".restore", dir=target.parent)
        os.close(fd)
    except OSError as e:
        raise BackupError(f"Could not restore {target.name}: {e.strerror or e}", backup_path=str(backup)) from e
    try:
        shutil.copy2(backup, tmp_name)
        os.replace(tmp_name, target)
    except OSError as e:
        raise BackupError(f"Could not restore {target.name}: {e.strerror or e}", backup_path=str(backup)) from e
    finally:
        Path(tmp_name).unlink(missing_ok=True)
