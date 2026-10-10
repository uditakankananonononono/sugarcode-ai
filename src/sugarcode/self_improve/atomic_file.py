"""Single-file atomic replacement helper, integrated after local verification.

Contract
--------
``atomic_write_text(path, text)`` / ``atomic_write_bytes(path, data)`` replace
the content of ONE file so that a reader after any failure sees either the
complete old content or the complete new content, never a truncated mix.

Policy:
* Encoding happens before any filesystem change. Text is encoded as UTF-8
  strictly; an encode error leaves the target and directory untouched.
  Callers must serialize (and validate, see SC-J02/J04) BEFORE calling. This
  module does no JSON handling and defines no payload policy.
* The temp file is created in the SAME directory as the target (so rename is
  on one filesystem) with O_CREAT|O_EXCL and a unique name
  ``.<name>.<random>.tmp``. The directory must already exist; none is created.
* Data is written in a loop (short writes handled), flushed and fsync'd, then
  ``os.replace`` swaps it in, then the directory is fsync'd where supported.
* Any failure before the replace removes the temp file and re-raises; the old
  target is unchanged. If cleanup itself fails the original error still wins.
* Mode: an existing regular target keeps its permission bits; a new target
  gets 0o600 unless ``mode`` is given. Ownership/ACLs/xattrs are not copied.
* Symlink or non-regular targets are refused (replacing would clobber the link
  or fail unpredictably).
* If the replace succeeded but the directory fsync failed, the new state IS in
  place; ``AtomicDurabilityError`` (with ``replaced = True``) is raised so the
  caller can tell this apart from "nothing changed".

Non-claims: single file only. No cross-file transaction, no exactly-once, no
locking between processes (callers keep their own lock, as gate/registry do
with shared path-keyed reentrant locks and POSIX advisory sidecars). Durability depends on OS/filesystem honoring fsync; on
Windows directory fsync is skipped and os.replace atomicity is as documented
by the platform. Stale ``.tmp`` files can remain after a hard crash (power
loss/kill); they are never read as state.
"""
from __future__ import annotations

import os
import stat
import uuid
from pathlib import Path


class AtomicWriteError(OSError):
    """Replacement failed; the target was left unchanged."""

    replaced = False


class AtomicDurabilityError(AtomicWriteError):
    """New content is in place but the directory sync did not complete."""

    replaced = True


class _Ops:
    """OS seam so tests can inject failures at each step."""

    open = staticmethod(os.open)
    write = staticmethod(os.write)
    fsync = staticmethod(os.fsync)
    fchmod = staticmethod(os.fchmod)
    close = staticmethod(os.close)
    replace = staticmethod(os.replace)
    unlink = staticmethod(os.unlink)


ops = _Ops()


def _fsync_dir(directory: Path) -> None:
    flag = getattr(os, "O_DIRECTORY", None)
    if flag is None or os.name == "nt":
        return  # platform cannot open directories; documented caveat
    fd = ops.open(str(directory), os.O_RDONLY | flag)
    try:
        ops.fsync(fd)
    finally:
        ops.close(fd)


def atomic_write_bytes(path: Path | str, data: bytes, *, mode: int | None = None) -> None:
    if type(data) is not bytes:
        raise TypeError("data must be exact bytes")
    target = Path(path)
    directory = target.parent
    try:
        info = os.lstat(target)
    except FileNotFoundError:
        info = None
    if info is not None and not stat.S_ISREG(info.st_mode):
        raise AtomicWriteError(f"refusing non-regular target {target}")
    preserve_mode = mode is None and info is not None
    if mode is None:
        mode = stat.S_IMODE(info.st_mode) if info is not None else 0o600
    temp = directory / f".{target.name}.{uuid.uuid4().hex}.tmp"
    fd = ops.open(str(temp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    fd_open = True
    try:
        if preserve_mode:
            ops.fchmod(fd, mode)  # os.open alone would mask old bits through umask
        view = memoryview(data)
        while view:
            written = ops.write(fd, view)
            if written <= 0:
                raise AtomicWriteError("zero-length write")
            view = view[written:]
        ops.fsync(fd)
        fd_open = False
        ops.close(fd)
        ops.replace(str(temp), str(target))
    except BaseException:
        if fd_open:
            try:
                ops.close(fd)
            except OSError:
                pass
        try:
            ops.unlink(str(temp))
        except OSError:
            pass
        raise
    try:
        _fsync_dir(directory)
    except OSError as exc:
        raise AtomicDurabilityError(str(exc)) from exc


def atomic_write_text(path: Path | str, text: str, *, mode: int | None = None) -> None:
    if type(text) is not str:
        raise TypeError("text must be exact str")
    atomic_write_bytes(path, text.encode("utf-8"), mode=mode)  # strict; before any I/O
