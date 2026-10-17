"""Creating and restoring backups (``rcg.inp_manage.backups``) and ``rcg.restore``."""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path

import pytest

from rcg.exceptions import BackupError, ModelOperationError, RCGError
from rcg.inp_manage import backups, writer
from rcg.service import apply, restore


def test_restore_puts_the_backup_back_and_keeps_it(example_inp, urban_params):
    original = example_inp.read_bytes()
    result = apply(example_inp, urban_params)
    assert result.backup_path is not None
    restore(result.backup_path, result.output_path, expected_sha256=result.written_sha256)
    assert example_inp.read_bytes() == original
    assert result.backup_path.read_bytes() == original
    assert [p.name for p in example_inp.parent.iterdir() if p.name.endswith(".restore")] == []


def test_restore_refuses_when_the_file_changed_since(example_inp, urban_params):
    result = apply(example_inp, urban_params)
    assert result.backup_path is not None
    edited = example_inp.read_bytes() + b"\n; edited in SWMM\n"
    example_inp.write_bytes(edited)
    with pytest.raises(BackupError, match="changed since RCG wrote it") as info:
        restore(result.backup_path, result.output_path, expected_sha256=result.written_sha256)
    assert info.value.backup_path == str(result.backup_path)
    assert example_inp.read_bytes() == edited


def test_restore_refuses_when_the_file_was_deleted(example_inp, urban_params):
    result = apply(example_inp, urban_params)
    assert result.backup_path is not None
    example_inp.unlink()
    with pytest.raises(BackupError, match="changed"):
        restore(result.backup_path, result.output_path, expected_sha256=result.written_sha256)
    assert not example_inp.exists()


def test_restore_without_fingerprint_overwrites(example_inp, urban_params):
    original = example_inp.read_bytes()
    result = apply(example_inp, urban_params)
    assert result.backup_path is not None
    example_inp.write_bytes(b"anything")
    restore(result.backup_path, result.output_path)
    assert example_inp.read_bytes() == original


def test_restore_missing_backup(example_inp, tmp_path):
    missing = tmp_path / "gone.inp"
    with pytest.raises(BackupError, match="no longer exists") as info:
        restore(missing, example_inp)
    assert isinstance(info.value, RCGError)
    assert info.value.backup_path == str(missing)


@pytest.mark.skipif(sys.platform == "win32" or os.geteuid() == 0, reason="needs POSIX permissions as non-root")
def test_restore_io_error_is_a_backup_error(example_inp, urban_params):
    result = apply(example_inp, urban_params)
    assert result.backup_path is not None
    written = example_inp.read_bytes()
    example_inp.parent.chmod(0o500)  # no new files (the temporary copy) in the folder
    try:
        with pytest.raises(BackupError, match="Could not restore"):
            restore(result.backup_path, result.output_path)
    finally:
        example_inp.parent.chmod(0o700)
    assert example_inp.read_bytes() == written


def test_file_sha256(tmp_path):
    path = tmp_path / "a.inp"
    path.write_bytes(b"abc")
    assert backups.file_sha256(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert backups.file_sha256(tmp_path / "missing.inp") is None


def test_create_backup_accepts_str_and_coerces_to_path(tmp_path):
    model = tmp_path / "model.inp"
    model.write_text("content", encoding="utf-8")
    backup = backups.create_backup(str(model))
    assert isinstance(backup, Path)
    assert backup.is_file()
    assert backup.read_text(encoding="utf-8") == "content"


def test_create_backup_cleans_up_target_on_copy_error(tmp_path, monkeypatch):
    model = tmp_path / "model.inp"
    model.write_text("content", encoding="utf-8")

    def broken_copy2(src, dst):
        raise OSError("Disk full (ENOSPC)")

    monkeypatch.setattr(shutil, "copy2", broken_copy2)
    with pytest.raises(ModelOperationError, match="Cannot create backup"):
        backups.create_backup(model)

    backup_dir = tmp_path / backups.BACKUP_DIR_NAME
    assert list(backup_dir.glob("*.inp")) == []


def test_create_backup_calls_prune_backups(tmp_path, monkeypatch):
    model = tmp_path / "model.inp"
    model.write_text("content", encoding="utf-8")
    pruned_targets: list[Path] = []
    monkeypatch.setattr(backups, "prune_backups", lambda p: pruned_targets.append(Path(p)) or [])
    backups.create_backup(model)
    assert pruned_targets == [model]


def test_restore_backup_rejects_empty_file(tmp_path):
    empty_backup = tmp_path / "empty_backup.inp"
    empty_backup.touch()
    target = tmp_path / "target.inp"
    target.write_bytes(b"target data")

    with pytest.raises(BackupError, match=r"empty \(0 bytes\)") as info:
        backups.restore_backup(empty_backup, target)

    assert info.value.backup_path == str(empty_backup)
    assert target.read_bytes() == b"target data"


def test_restore_backup_accepts_str_paths(tmp_path):
    backup = tmp_path / "backup.inp"
    backup.write_bytes(b"restored content")
    target = tmp_path / "target.inp"
    target.write_bytes(b"old content")

    backups.restore_backup(str(backup), str(target))
    assert target.read_bytes() == b"restored content"


def test_prune_backups_nonexistent_or_empty_dir(tmp_path):
    model = tmp_path / "sub" / "model.inp"
    assert backups.prune_backups(model) == []
    assert backups.prune_backups(str(model)) == []

    backup_dir = tmp_path / backups.BACKUP_DIR_NAME
    backup_dir.mkdir()
    assert backups.prune_backups(tmp_path / "model.inp") == []


def test_prune_backups_keeps_single_backup_even_if_old(tmp_path):
    backup_dir = tmp_path / backups.BACKUP_DIR_NAME
    backup_dir.mkdir()
    old_backup = backup_dir / "model_backup_20200101_000000_000000.inp"
    old_backup.write_text("old", encoding="utf-8")
    old_time = time.time() - 100 * 86400.0
    os.utime(old_backup, (old_time, old_time))

    pruned = backups.prune_backups(tmp_path / "model.inp", max_backups=5, max_age_days=30.0)
    assert pruned == []
    assert old_backup.exists()


def test_prune_backups_max_backups_bound(tmp_path):
    backup_dir = tmp_path / backups.BACKUP_DIR_NAME
    backup_dir.mkdir()
    now = time.time()
    created = []
    for i in range(15):
        b = backup_dir / f"model_backup_{i:02d}.inp"
        b.write_text(f"backup {i}", encoding="utf-8")
        t = now - (15 - i) * 10
        os.utime(b, (t, t))
        created.append(b)

    pruned = backups.prune_backups(tmp_path / "model.inp", max_backups=10, max_age_days=365.0)
    assert len(pruned) == 5
    assert set(pruned) == set(created[:5])
    remaining = sorted(backup_dir.glob("model_backup_*.inp"))
    assert set(remaining) == set(created[5:])


def test_prune_backups_max_age_days(tmp_path):
    backup_dir = tmp_path / backups.BACKUP_DIR_NAME
    backup_dir.mkdir()
    now = time.time()
    ages = [50, 40, 5, 2]
    files = []
    for i, age in enumerate(ages):
        b = backup_dir / f"model_backup_{i:02d}.inp"
        b.write_text(f"backup {i}", encoding="utf-8")
        t = now - age * 86400.0
        os.utime(b, (t, t))
        files.append(b)

    pruned = backups.prune_backups(tmp_path / "model.inp", max_backups=10, max_age_days=30.0)
    assert set(pruned) == {files[0], files[1]}
    assert files[2].exists() and files[3].exists()


def test_prune_backups_all_expired_keeps_newest(tmp_path):
    backup_dir = tmp_path / backups.BACKUP_DIR_NAME
    backup_dir.mkdir()
    now = time.time()
    ages = [80, 70, 60]
    files = []
    for i, age in enumerate(ages):
        b = backup_dir / f"model_backup_{i:02d}.inp"
        b.write_text(f"backup {i}", encoding="utf-8")
        t = now - age * 86400.0
        os.utime(b, (t, t))
        files.append(b)

    pruned = backups.prune_backups(tmp_path / "model.inp", max_backups=10, max_age_days=30.0)
    assert set(pruned) == {files[0], files[1]}
    assert files[2].exists()


def test_prune_backups_isolates_models(tmp_path):
    backup_dir = tmp_path / backups.BACKUP_DIR_NAME
    backup_dir.mkdir()
    now = time.time()
    alpha_files = []
    beta_files = []
    for i in range(5):
        a = backup_dir / f"alpha_backup_{i:02d}.inp"
        a.write_text(f"alpha {i}", encoding="utf-8")
        t = now - (10 - i) * 10
        os.utime(a, (t, t))
        alpha_files.append(a)

        b = backup_dir / f"beta_backup_{i:02d}.inp"
        b.write_text(f"beta {i}", encoding="utf-8")
        os.utime(b, (t, t))
        beta_files.append(b)

    pruned = backups.prune_backups(tmp_path / "alpha.inp", max_backups=2)
    assert set(pruned) == set(alpha_files[:3])
    assert set(backup_dir.glob("alpha_backup_*.inp")) == set(alpha_files[3:])
    assert set(backup_dir.glob("beta_backup_*.inp")) == set(beta_files)


def test_prune_backups_swallows_oserror_on_unlink(tmp_path, monkeypatch):
    backup_dir = tmp_path / backups.BACKUP_DIR_NAME
    backup_dir.mkdir()
    for i in range(3):
        b = backup_dir / f"model_backup_{i:02d}.inp"
        b.write_text(f"backup {i}", encoding="utf-8")

    def broken_unlink(path, missing_ok=True):
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "unlink", broken_unlink)
    pruned = backups.prune_backups(tmp_path / "model.inp", max_backups=1)
    assert pruned == []


def test_restore_backup_fsync_called(example_inp, urban_params, monkeypatch):
    result = apply(example_inp, urban_params)
    assert result.backup_path is not None
    fsync_fds: list[int] = []
    real_fsync = os.fsync

    def tracked_fsync(fd):
        fsync_fds.append(fd)
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", tracked_fsync)
    restore(result.backup_path, result.output_path)
    assert len(fsync_fds) >= 1


def test_fsync_dir_posix_lifecycle(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")
    calls: list[str] = []

    def mock_open(path, flags):
        calls.append("open")
        return 42

    def mock_fsync(fd):
        assert fd == 42
        calls.append("fsync")

    def mock_close(fd):
        assert fd == 42
        calls.append("close")

    monkeypatch.setattr(os, "open", mock_open)
    monkeypatch.setattr(os, "fsync", mock_fsync)
    monkeypatch.setattr(os, "close", mock_close)

    backups._fsync_dir("/some/dir")
    assert calls == ["open", "fsync", "close"]


def test_fsync_dir_posix_fsync_fails_closes_fd(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")
    calls: list[str] = []

    def mock_open(path, flags):
        calls.append("open")
        return 77

    def mock_fsync(fd):
        calls.append("fsync")
        raise OSError(22, "Invalid argument (NFS/CIFS)")

    def mock_close(fd):
        assert fd == 77
        calls.append("close")

    monkeypatch.setattr(os, "open", mock_open)
    monkeypatch.setattr(os, "fsync", mock_fsync)
    monkeypatch.setattr(os, "close", mock_close)

    backups._fsync_dir("/some/dir")
    assert calls == ["open", "fsync", "close"]


def test_fsync_dir_non_posix_noop(monkeypatch):
    monkeypatch.setattr(os, "name", "nt")

    def mock_open(path, flags):
        raise AssertionError("os.open should not be called on non-posix")

    monkeypatch.setattr(os, "open", mock_open)
    backups._fsync_dir("/some/dir")


def test_write_atomic_invokes_fsync_dir(example_inp, urban_params, monkeypatch):
    fsync_dirs: list[Path] = []
    monkeypatch.setattr(writer, "_fsync_dir", lambda d: fsync_dirs.append(Path(d)))

    apply(example_inp, urban_params, backup=False)
    assert fsync_dirs == [example_inp.parent]
