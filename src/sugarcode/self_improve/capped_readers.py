"""SC-F02 PREP ONLY: bounded file input, independent of JSON codecs.

No caller is wired to these readers. Limits have no inferred/default policy.
All size checks complete before any UTF-8 or JSON decode. Files are read-only.
"""
from __future__ import annotations

from pathlib import Path


class InputLimitExceeded(ValueError):
    """A physical byte budget was exceeded; source bytes were not changed."""

    def __init__(self, scope: str, limit: int, *, line_number: int | None = None):
        self.scope = scope
        self.limit = limit
        self.line_number = line_number
        suffix = "" if line_number is None else f" at physical line {line_number}"
        super().__init__(f"{scope} byte limit {limit} exceeded{suffix}")


def _budget(name: str, value: int, *, positive: bool = False) -> None:
    if type(value) is not int or value < (1 if positive else 0):
        raise ValueError(f"{name} must be an exact {'positive' if positive else 'nonnegative'} int")


def _read(path: Path | str, *, max_file_bytes: int,
          max_line_bytes: int | None, chunk_bytes: int) -> bytes:
    _budget("max_file_bytes", max_file_bytes)
    _budget("chunk_bytes", chunk_bytes, positive=True)
    if max_line_bytes is not None:
        _budget("max_line_bytes", max_line_bytes)
    retained = bytearray()
    line_size = 0
    line_number = 1
    # Unbuffered binary reads avoid hidden read-ahead beyond requested bytes.
    # No stat-size assumption: growth or a stale size cannot bypass byte counts.
    with Path(path).open("rb", buffering=0) as source:
        while True:
            request = min(chunk_bytes, max_file_bytes - len(retained) + 1)
            if max_line_bytes is not None:
                request = min(request, max_line_bytes - line_size + 1)
            chunk = source.read(request)
            if not chunk:
                break
            if len(retained) + len(chunk) > max_file_bytes:
                raise InputLimitExceeded("file", max_file_bytes)
            if max_line_bytes is not None:
                start = 0
                while start < len(chunk):
                    newline = chunk.find(b"\n", start)
                    end = len(chunk) if newline < 0 else newline + 1
                    line_size += end - start
                    if line_size > max_line_bytes:
                        raise InputLimitExceeded("line", max_line_bytes,
                                                 line_number=line_number)
                    if newline >= 0:
                        line_size = 0
                        line_number += 1
                    start = end
            retained.extend(chunk)
    return bytes(retained)


def read_capped_bytes(path: Path | str, *, max_file_bytes: int,
                      chunk_bytes: int = 65536) -> bytes:
    """Read at most a caller-selected byte cap, plus one refusal probe byte."""
    return _read(path, max_file_bytes=max_file_bytes,
                 max_line_bytes=None, chunk_bytes=chunk_bytes)


def read_capped_utf8(path: Path | str, *, max_file_bytes: int,
                     chunk_bytes: int = 65536) -> str:
    """Return strict UTF-8 only after the full file passes its byte budget.

    BOM is retained, not silently removed. Invalid UTF-8 raises UnicodeDecodeError.
    JSON parsing/schema/authentication remain separate caller responsibilities.
    """
    return read_capped_bytes(path, max_file_bytes=max_file_bytes,
                             chunk_bytes=chunk_bytes).decode("utf-8", errors="strict")


def read_capped_utf8_lines(path: Path | str, *, max_file_bytes: int,
                           max_line_bytes: int, chunk_bytes: int = 65536) -> tuple[str, ...]:
    """Read all bounded LF records before returning any decoded rows.

    Line budgets include physical terminators (LF or CRLF). An unterminated final
    line is allowed. CR immediately before LF is removed in returned records;
    bare CR and Unicode line separators are data, not record boundaries. Empty
    physical records are retained; empty input/trailing LF has no phantom record.
    """
    _budget("max_line_bytes", max_line_bytes)
    text = _read(path, max_file_bytes=max_file_bytes,
                 max_line_bytes=max_line_bytes, chunk_bytes=chunk_bytes).decode(
                     "utf-8", errors="strict")
    if not text:
        return ()
    lines = text.split("\n")
    if text.endswith("\n"):
        lines.pop()
    # Only LF-terminated records have their preceding CR removed.
    terminated_count = len(lines) if text.endswith("\n") else len(lines) - 1
    for index in range(terminated_count):
        if lines[index].endswith("\r"):
            lines[index] = lines[index][:-1]
    return tuple(lines)
