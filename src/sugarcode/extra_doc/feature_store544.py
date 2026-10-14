"""Row 544: Feature Store Design - Manages ML features.

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


def materialize_features(rows):
    """Rows: (entity, feature, timestamp 0..1,000,000, integer_value).
    Materialize latest supplied value for each entity/feature pair. Duplicate
    entity/feature/timestamp refused. In-memory snapshot only, not persistent
    online/offline serving, point-in-time joins or training/serving consistency.
    """
    _rows(rows, 4)
    for entity, feature, timestamp, value in rows:
        _label(entity)
        _label(feature)
        _integer(timestamp, 0, 1000000)
        _integer(value, -1000000, 1000000)
    if len({(x[0],x[1],x[2]) for x in rows}) != len(rows):
        raise ValueError('duplicate entity feature timestamp')
    pairs = sorted({(x[0],x[1]) for x in rows})
    snapshot = []
    for entity, feature in pairs:
        selected = max((row for row in rows if row[:2]==(entity,feature)),key=lambda x:x[2])
        snapshot.append(selected)
    return {'features': snapshot, 'observation_count': len(rows)}
