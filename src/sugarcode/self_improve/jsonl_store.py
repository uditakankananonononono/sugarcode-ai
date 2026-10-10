"""Cooperating bounded JSONL append. Not atomic append or crash durability.

Reads may create a stable advisory sidecar. Noncooperating edits/alias changes
are outside the shared_state_lock contract. Whole-history work remains O(history).
"""
import os
from pathlib import Path

from .capped_readers import read_capped_bytes, InputLimitExceeded, _budget
from .state_lock import shared_state_lock


def _lines(raw, max_line_bytes):
    _budget("max_line_bytes", max_line_bytes)
    # Admission precedes UTF-8/schema decode. Include terminators in byte budgets.
    chunks = raw.split(b'\n')
    for number, chunk in enumerate(chunks, 1):
        terminated = number < len(chunks)
        if len(chunk) + int(terminated) > max_line_bytes:
            raise InputLimitExceeded('line', max_line_bytes, line_number=number)
    text = raw.decode('utf-8', errors='strict')
    rows = text.split('\n')
    if raw.endswith(b'\n'):
        rows.pop()
    if not raw:
        return ()
    for i in range(len(rows) if raw.endswith(b'\n') else len(rows)-1):
        if rows[i].endswith('\r'):
            rows[i] = rows[i][:-1]
    return tuple(rows)


def read_jsonl(path, *, max_file_bytes, max_line_bytes, decode):
    """Read/validate under the same advisory path lock used by append."""
    _budget("max_file_bytes", max_file_bytes)
    path = Path(path)
    with shared_state_lock(path):
        raw = read_capped_bytes(path, max_file_bytes=max_file_bytes) if path.exists() else b''
        return decode(_lines(raw, max_line_bytes))


def append_jsonl(path, encoded, *, max_file_bytes, max_line_bytes, decode):
    """Validate full prior history and admission under lock, then append.

    A valid unterminated final row gains one LF, charged to both budgets.
    Short writes are completed; errors can leave a partial row. No rollback,
    fsync, repair, cleanup, cross-file transaction or exactly-once guarantee.
    """
    _budget('max_line_bytes', max_line_bytes)
    if type(encoded) is not bytes or not encoded.endswith(b'\n') or b'\n' in encoded[:-1]:
        raise ValueError('append requires one LF-terminated physical record')
    if len(encoded) > max_line_bytes:
        raise InputLimitExceeded('line', max_line_bytes)
    _budget("max_file_bytes", max_file_bytes)
    path = Path(path)
    with shared_state_lock(path):
        prior = read_capped_bytes(path, max_file_bytes=max_file_bytes) if path.exists() else b''
        decode(_lines(prior, max_line_bytes))
        delimiter = b'\n' if prior and not prior.endswith(b'\n') else b''
        if delimiter and len(prior.rsplit(b'\n', 1)[-1]) + 1 > max_line_bytes:
            raise InputLimitExceeded('line', max_line_bytes, line_number=prior.count(b'\n')+1)
        output = delimiter + encoded
        if len(prior) + len(output) > max_file_bytes:
            raise InputLimitExceeded('file', max_file_bytes)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            view = memoryview(output)
            while view:
                count = os.write(fd, view)
                if count <= 0:
                    raise OSError('JSONL append made no progress')
                view = view[count:]
        finally:
            os.close(fd)
