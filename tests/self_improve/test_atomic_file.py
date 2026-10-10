"""AUTHORED, NOT RUN. Tests for self_improve.atomic_file (SC-F01 prep)."""
from __future__ import annotations

import os
import stat

import pytest

from sugarcode.self_improve import atomic_file as af


def _snapshot(directory):
    return {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}


def test_creates_new_file_with_private_mode(tmp_path):
    t = tmp_path / "s.json"
    af.atomic_write_text(t, "hello")
    assert t.read_text(encoding="utf-8") == "hello"
    if os.name != "nt":
        assert stat.S_IMODE(t.stat().st_mode) == 0o600
    assert [p.name for p in tmp_path.iterdir()] == ["s.json"]


def test_replaces_existing_and_keeps_mode(tmp_path):
    t = tmp_path / "s.json"
    t.write_text("old")
    if os.name != "nt":
        t.chmod(0o640)
    af.atomic_write_text(t, "new")
    assert t.read_text() == "new"
    if os.name != "nt":
        assert stat.S_IMODE(t.stat().st_mode) == 0o640
    assert [p.name for p in tmp_path.iterdir()] == ["s.json"]


def test_explicit_mode_for_new_file(tmp_path):
    if os.name == "nt":
        pytest.skip("posix modes")
    t = tmp_path / "s"
    af.atomic_write_bytes(t, b"x", mode=0o644)
    # os.open applies the process umask, so group/other bits are at most 0o044
    assert stat.S_IMODE(t.stat().st_mode) & ~0o644 == 0
    assert stat.S_IMODE(t.stat().st_mode) & 0o600 == 0o600


def test_large_payload_roundtrip_with_short_writes(tmp_path, monkeypatch):
    real = os.write
    monkeypatch.setattr(af.ops, "write", lambda fd, b: real(fd, bytes(b[:7])))
    data = os.urandom(5000)
    t = tmp_path / "b"
    af.atomic_write_bytes(t, data)
    assert t.read_bytes() == data


def test_encode_failure_touches_nothing(tmp_path):
    t = tmp_path / "s"
    t.write_text("old")
    before = _snapshot(tmp_path)
    with pytest.raises(UnicodeEncodeError):
        af.atomic_write_text(t, "bad \ud800 surrogate")
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("bad", ["x", 5, None, bytearray(b"x")])
def test_bytes_type_checks(tmp_path, bad):
    t = tmp_path / "s"
    t.write_text("old")
    with pytest.raises(TypeError):
        af.atomic_write_bytes(t, bad)
    assert t.read_text() == "old"


def test_text_type_check(tmp_path):
    with pytest.raises(TypeError):
        af.atomic_write_text(tmp_path / "s", b"x")


@pytest.mark.parametrize("step", ["open", "write", "fsync", "close", "replace"])
def test_failure_injection_preserves_old_state_and_leaks_no_temp(tmp_path, monkeypatch, step):
    t = tmp_path / "s"
    t.write_text("old")
    before = _snapshot(tmp_path)
    real = getattr(af.ops, step)
    calls = {"n": 0}

    def boom(*a, **k):
        calls["n"] += 1
        if step == "fsync" or step == "close":
            # first fsync/close belongs to the data file; let cleanup close work
            if calls["n"] == 1:
                if step == "close":
                    real(*a, **k)
                raise OSError(5, "injected")
            return real(*a, **k)
        raise OSError(5, "injected")

    monkeypatch.setattr(af.ops, step, boom)
    with pytest.raises(OSError):
        af.atomic_write_text(t, "new content")
    monkeypatch.undo()
    assert _snapshot(tmp_path) == before


def test_partial_write_then_error_removes_temp(tmp_path, monkeypatch):
    t = tmp_path / "s"
    t.write_text("old")
    real = os.write
    state = {"n": 0}

    def flaky(fd, b):
        state["n"] += 1
        if state["n"] == 2:
            raise OSError(28, "no space")
        return real(fd, bytes(b[:3]))

    monkeypatch.setattr(af.ops, "write", flaky)
    with pytest.raises(OSError):
        af.atomic_write_text(t, "0123456789")
    monkeypatch.undo()
    assert _snapshot(tmp_path) == {"s": b"old"}


def test_zero_length_write_is_error(tmp_path, monkeypatch):
    t = tmp_path / "s"
    t.write_text("old")
    monkeypatch.setattr(af.ops, "write", lambda fd, b: 0)
    with pytest.raises(af.AtomicWriteError):
        af.atomic_write_text(t, "new")
    monkeypatch.undo()
    assert _snapshot(tmp_path) == {"s": b"old"}


def test_cleanup_failure_does_not_mask_original_error(tmp_path, monkeypatch):
    t = tmp_path / "s"
    t.write_text("old")

    def no_replace(a, b):
        raise PermissionError(13, "original")

    def no_unlink(p):
        raise OSError(1, "cleanup")

    monkeypatch.setattr(af.ops, "replace", no_replace)
    monkeypatch.setattr(af.ops, "unlink", no_unlink)
    with pytest.raises(PermissionError):
        af.atomic_write_text(t, "new")
    monkeypatch.undo()
    assert t.read_text() == "old"  # temp may remain only because cleanup was sabotaged


def test_dir_fsync_failure_reports_replaced(tmp_path, monkeypatch):
    if not hasattr(os, "O_DIRECTORY") or os.name == "nt":
        pytest.skip("no dir fsync on this platform")
    t = tmp_path / "s"
    t.write_text("old")
    real = af.ops.fsync
    n = {"c": 0}

    def second_fails(fd):
        n["c"] += 1
        if n["c"] == 2:
            raise OSError(5, "dir sync")
        return real(fd)

    monkeypatch.setattr(af.ops, "fsync", second_fails)
    with pytest.raises(af.AtomicDurabilityError) as ei:
        af.atomic_write_text(t, "new")
    monkeypatch.undo()
    assert ei.value.replaced is True
    assert t.read_text() == "new"
    assert [p.name for p in tmp_path.iterdir()] == ["s"]


def test_refuses_symlink_target(tmp_path):
    if os.name == "nt":
        pytest.skip("symlink")
    real = tmp_path / "real"
    real.write_text("keep")
    link = tmp_path / "link"
    link.symlink_to(real)
    with pytest.raises(af.AtomicWriteError):
        af.atomic_write_text(link, "new")
    assert real.read_text() == "keep" and link.is_symlink()


def test_refuses_directory_target(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    with pytest.raises(af.AtomicWriteError):
        af.atomic_write_text(d, "x")
    assert d.is_dir()


def test_missing_parent_directory_raises_and_creates_nothing(tmp_path):
    with pytest.raises(FileNotFoundError):
        af.atomic_write_text(tmp_path / "nope" / "s", "x")
    assert not (tmp_path / "nope").exists()


def test_temp_name_is_same_directory_and_dotted(tmp_path, monkeypatch):
    seen = []
    real = af.ops.replace
    monkeypatch.setattr(af.ops, "replace", lambda a, b: (seen.append(a), real(a, b))[1])
    af.atomic_write_text(tmp_path / "s", "x")
    assert os.path.dirname(seen[0]) == str(tmp_path)
    assert os.path.basename(seen[0]).startswith(".s.") and seen[0].endswith(".tmp")
