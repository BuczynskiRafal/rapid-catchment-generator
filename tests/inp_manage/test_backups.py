"""Creating and restoring backups (``rcg.inp_manage.backups``) and ``rcg.restore``."""

from __future__ import annotations

import os
import sys

import pytest

from rcg.exceptions import BackupError, RCGError
from rcg.inp_manage import backups
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
