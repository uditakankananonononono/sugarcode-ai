"""Row 540: Batch Processing - Handles bulk data.

Bounded planning aid over caller supplied rows. No external actions, persistence,
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


def process_batches(rows):
    """Rows: (record_id, batch_id 0..31, integer_value +/-1,000,000).
    Process supplied bounded records into sorted batch aggregates. Record IDs
    must be unique. Pure in-memory bulk transform, no scheduler, IO or retries.
    """
    _rows(rows, 3)
    for record, batch, value in rows:
        _label(record)
        _integer(batch, 0, 31)
        _integer(value, -1000000, 1000000)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate record')
    result = []
    for batch in sorted({x[1] for x in rows}):
        values = [value for _, group, value in rows if group==batch]
        result.append((batch,len(values),sum(values),min(values),max(values)))
    return {'batches': result, 'record_count': len(rows), 'total': sum(x[2] for x in rows)}
