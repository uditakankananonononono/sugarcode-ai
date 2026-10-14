"""Row 541: Lambda Architecture - Combines batch and stream.

SCOPED planning aid over caller supplied rows. No external actions, persistence,
capability development evidence, organization quality, or optimal policy claim.
Explicit import only; 1..32 tuple rows. Labels are lowercase ASCII identifiers.
"""
import re

LABEL = re.compile(r"[a-z][a-z0-9_]{0,23}\Z")


def _label(value):
    if type(value) is not str:
        raise TypeError('exact string label required')
    if len(value) > 24 or LABEL.fullmatch(value) is None:
        raise ValueError('label must be 1..24 lowercase identifier characters')


def _integer(value, low, high):
    if type(value) is not int:
        raise TypeError('exact nonbool integer required')
    if not low <= value <= high:
        raise ValueError('integer outside declared range')


def _rows(rows, arity):
    if type(rows) is not list:
        raise TypeError('exact list required')
    if not 1 <= len(rows) <= 32:
        raise ValueError('row count must be 1..32')
    for row in rows:
        if type(row) is not tuple:
            raise TypeError('exact tuple row required')
        if len(row) != arity:
            raise ValueError('wrong row arity')


def merge_batch_stream(rows):
    """Rows: (key, logical_version 0..1,000,000, value, source_bit).
    source_bit 0=batch snapshot, 1=stream update. Reconcile latest version per
    key; stream overrides batch at equal version. Duplicate key/version/source
    is refused, including conflicting values. Pure in-memory lambda merge, not
    a distributed architecture or event-time/watermark/partition guarantee.
    """
    _rows(rows, 4)
    for key, version, value, source in rows:
        _label(key)
        _integer(version, 0, 1000000)
        _integer(value, -1000000, 1000000)
        _integer(source, 0, 1)
    if len({(x[0],x[1],x[3]) for x in rows}) != len(rows):
        raise ValueError('duplicate key version source')
    merged = []
    for key in sorted({x[0] for x in rows}):
        latest = max((row for row in rows if row[0]==key), key=lambda x:(x[1],x[3]))
        merged.append(latest)
    return {'view': merged, 'input_count': len(rows)}
