"""Row 477: Communication Planning - Structures messaging.

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


def plan_messages(rows):
    """Rows: (audience, channel, fact_id, owner, day), day 0..365.

    Return a chronological supplied-fact matrix. No messages are authored,
    persisted, sent, or approved. Duplicate full rows are refused.
    """
    _rows(rows, 5)
    for audience, channel, fact_id, owner, day in rows:
        for value in (audience, channel, fact_id, owner):
            _label(value)
        _integer(day, 0, 365)
    if len(set(rows)) != len(rows):
        raise ValueError('duplicate message row')
    ordered = sorted(rows, key=lambda x: (x[4], x[0], x[1], x[2], x[3]))
    return {'matrix': ordered,
            'audiences': sorted({x[0] for x in rows}),
            'channels': sorted({x[1] for x in rows}),
            'message_count': len(rows)}
