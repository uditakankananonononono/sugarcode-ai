"""Row 542: Kappa Architecture - Stream-only processing.

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


def replay_stream(rows):
    """Rows: (event_id, key, sequence 0..1,000,000, signed_delta).
    Replay only a supplied event log. Unique event IDs and per-key sequences
    are required. Events are sorted by sequence then ID; sum state per key and
    expose every transition. No batch snapshot, networking, persistence, window
    semantics, recovery or exactly-once external processing is claimed.
    """
    _rows(rows, 4)
    for event, key, sequence, delta in rows:
        _label(event)
        _label(key)
        _integer(sequence, 0, 1000000)
        _integer(delta, -1000000, 1000000)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate event')
    if len({(x[1],x[2]) for x in rows}) != len(rows):
        raise ValueError('duplicate key sequence')
    state = {}
    trace = []
    for event, key, sequence, delta in sorted(rows,key=lambda x:(x[2],x[0])):
        before = state.get(key,0)
        state[key] = before+delta
        trace.append((event,key,sequence,before,state[key]))
    return {'state': sorted(state.items()), 'trace': trace, 'events': len(rows)}
