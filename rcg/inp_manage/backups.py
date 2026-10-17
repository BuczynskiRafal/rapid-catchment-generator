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

__all__ = ["BACKUP_DIR_NAME", "create_backup", "file_sha256", "prune_backups", "restore_backup"]

BACKUP_DIR_NAME = ".rcg_backups"


def create_backup(path: str | Path) -> Path:
    """Copy ``path`` to ``<dir>/.rcg_backups/<stem>_backup_<timestamp><suffix>`` and return the copy.

    The name is reserved with an exclusive create, so a backup never replaces another one:
    when the timestamp repeats (the clock on Windows is coarse), ``_1``, ``_2``, ... is appended.
    """
    path = Path(path)
    backup_dir = path.parent / BACKUP_DIR_NAME
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target: Path | None = None
    try:
        backup_dir.mkdir(exist_ok=True)
        target = _reserve_backup_name(backup_dir, f"{path.stem}_backup_{stamp}", path.suffix)
        shutil.copy2(path, target)
    except OSError as e:
        if target is not None:
            try:
                target.unlink(missing_ok=True)
            except OSError:
                pass
        raise ModelOperationError(
            f"Cannot create backup in {backup_dir}: {e}", operation="backup", model_path=str(path)
        ) from e
    prune_backups(path)
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


def prune_backups(
    model_path: str | Path,
    *,
    max_backups: int = 10,
    max_age_days: float = 30.0,
) -> list[Path]:
    """Remove older backups for ``model_path`` to bound disk usage.

    Always keeps at least the newest backup. Never raises exceptions.
    """
    model = Path(model_path)
    backup_dir = model.parent / BACKUP_DIR_NAME
    if not backup_dir.is_dir():
        return []

    pattern = f"{model.stem}_backup_*{model.suffix}"
    try:
        backups = sorted(
            [p for p in backup_dir.glob(pattern) if p.is_file()],
            key=lambda p: (p.stat().st_mtime, p.name),
            reverse=True,
        )
    except OSError:
        return []

    if len(backups) <= 1:
        return []

    now = datetime.now().timestamp()
    cutoff_seconds = max_age_days * 86400.0
    pruned: list[Path] = []

    for i, b in enumerate(backups):
        # Never delete the newest backup (index 0)
        if i == 0:
            continue
        try:
            stat = b.stat()
            is_excess = i >= max_backups
            is_expired = (now - stat.st_mtime) > cutoff_seconds
            if is_excess or is_expired:
                b.unlink(missing_ok=True)
                pruned.append(b)
        except OSError:
            continue

    return pruned


def _fsync_dir(directory: Path | str) -> None:
    """Flush directory changes to persistent storage on POSIX systems with guaranteed descriptor cleanup."""
    if os.name != "posix":
        return
    try:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        dir_fd = os.open(str(directory), flags)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    except OSError:
        pass
    finally:
        os.close(dir_fd)


def restore_backup(backup: str | Path, target: str | Path, *, expected_sha256: str | None = None) -> None:
    """Copy *backup* back over *target* atomically; the backup is kept.

    Parameters
    ----------
    backup : str or Path
        Backup made by :func:`create_backup`.
    target : str or Path
        File to restore.
    expected_sha256 : str, optional
        Hex SHA-256 of *target* as RCG wrote it (:attr:`rcg.ApplyResult.written_sha256`).
        When given and *target* no longer matches (edited, replaced or deleted since),
        nothing is restored, so changes made elsewhere are never thrown away.

    Raises
    ------
    BackupError
        If the backup no longer exists, is empty (0 bytes), *target* changed since it
        was written, or the copy fails. *target* is never left half-written.
    """
    backup, target = Path(backup), Path(target)
    if not backup.is_file():
        raise BackupError(f"The backup no longer exists: {backup}", backup_path=str(backup))
    try:
        st_size = backup.stat().st_size
    except OSError as e:
        raise BackupError(f"Cannot inspect backup {backup}: {e}", backup_path=str(backup)) from e
    if st_size == 0:
        raise BackupError(f"The backup is empty (0 bytes): {backup}", backup_path=str(backup))
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
        with open(tmp_name, "r+b") as fh:
            os.fsync(fh.fileno())
        os.replace(tmp_name, target)
        _fsync_dir(target.parent)
    except OSError as e:
        raise BackupError(f"Could not restore {target.name}: {e.strerror or e}", backup_path=str(backup)) from e
    finally:
        Path(tmp_name).unlink(missing_ok=True)
