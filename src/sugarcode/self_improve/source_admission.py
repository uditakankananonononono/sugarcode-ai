"""Opt-in bounded source snapshots. No existing production caller is wired."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat

from .capped_readers import InputLimitExceeded


@dataclass(frozen=True)
class SourceLimits:
    """Explicit UTF-8 byte limits, not CPU/RSS budgets or permission grants."""
    code_bytes: int
    test_bytes: int

    def __post_init__(self) -> None:
        for value in (self.code_bytes, self.test_bytes):
            if type(value) is not int or value < 0:
                raise ValueError("source limits must be exact nonnegative integers")


@dataclass(frozen=True)
class SourceSnapshot:
    content: bytes
    text: str
    sha256: str


@dataclass(frozen=True)
class CandidateSnapshot:
    code: SourceSnapshot
    tests: SourceSnapshot


def _snapshot(raw: bytes, expected_sha256: str | None) -> SourceSnapshot:
    # Verify original bytes, never newline-normalized or decoded content.
    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None:
        if (type(expected_sha256) is not str or len(expected_sha256) != 64 or
                any(char not in "0123456789abcdef" for char in expected_sha256)):
            raise ValueError("expected digest must be lowercase SHA-256")
        if digest != expected_sha256:
            raise ValueError("source digest mismatch")
    return SourceSnapshot(raw, raw.decode("utf-8", errors="strict"), digest)


def admit_source_text(text: str, *, max_bytes: int,
                      expected_sha256: str | None = None) -> SourceSnapshot:
    """Cap encoded bytes without first allocating an unbounded UTF-8 copy.

    Exact builtin strings only. Existing caller string allocation already happened.
    A character-count lower bound rejects obviously oversized text before encode;
    bounded chunks check byte count. No code execution or Python syntax claim.
    """
    SourceLimits(max_bytes, 0)
    if type(text) is not str:
        raise ValueError("source must be an exact builtin string")
    if len(text) > max_bytes:
        raise InputLimitExceeded("source", max_bytes)
    raw = bytearray()
    for start in range(0, len(text), 16384):
        chunk = text[start:start + 16384].encode("utf-8", errors="strict")
        if len(raw) + len(chunk) > max_bytes:
            raise InputLimitExceeded("source", max_bytes)
        raw.extend(chunk)
    return _snapshot(bytes(raw), expected_sha256)


def read_source_snapshot(path: Path | str, *, max_bytes: int,
                         expected_sha256: str | None = None) -> SourceSnapshot:
    """One descriptor, cap+1 refusal probe, then hash and strict UTF-8.

    Linux/POSIX regular-file only; final symlink refused. NONBLOCK + fstat rejects
    FIFO/device before reading. Ancestors/path ownership/external writes untrusted;
    descriptor content may still change while reading. Fail closed without writes.
    """
    SourceLimits(max_bytes, 0)
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_NONBLOCK"):
        raise OSError("regular source descriptor admission unavailable")
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("source must be a regular file")
        raw = bytearray()
        while True:
            chunk = os.read(descriptor, min(65536, max_bytes - len(raw) + 1))
            if not chunk:
                break
            if len(raw) + len(chunk) > max_bytes:
                raise InputLimitExceeded("source", max_bytes)
            raw.extend(chunk)
        return _snapshot(bytes(raw), expected_sha256)
    finally:
        os.close(descriptor)


def admit_candidate_text(code: str, tests: str, *, limits: SourceLimits) -> CandidateSnapshot:
    """All-or-nothing result, code/test caps separate, no filesystem writes."""
    if type(limits) is not SourceLimits:
        raise ValueError("limits must be SourceLimits")
    return CandidateSnapshot(admit_source_text(code, max_bytes=limits.code_bytes),
                             admit_source_text(tests, max_bytes=limits.test_bytes))


def read_candidate_sources(code_path: Path | str, test_path: Path | str, *,
                           limits: SourceLimits, code_sha256: str | None = None,
                           test_sha256: str | None = None) -> CandidateSnapshot:
    """All-or-nothing return, not an atomic two-file snapshot or identity proof."""
    if type(limits) is not SourceLimits:
        raise ValueError("limits must be SourceLimits")
    return CandidateSnapshot(read_source_snapshot(code_path, max_bytes=limits.code_bytes,
                                                 expected_sha256=code_sha256),
                             read_source_snapshot(test_path, max_bytes=limits.test_bytes,
                                                  expected_sha256=test_sha256))
