"""Row 774: Inclusion - Includes all.

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


def review_participation_access(rows):
    """Rows: (participant_id, invited_bit, access_need_declared_bit,
    accommodation_available_bit). Flag not invited and declared access need
    without accommodation. No protected-trait inference, actual inclusion or
    accommodation provision/legal compliance. Supplied checklist only.
    """
    _rows(rows, 4)
    for participant,invited,need,available in rows:
        _label(participant)
        _integer(invited, 0, 1)
        _integer(need, 0, 1)
        _integer(available, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate participant')
    gaps=[]
    for participant,invited,need,available in sorted(rows):
        missing=[]
        if invited==0:
            missing.append('invitation')
        if need==1 and available==0:
            missing.append('accommodation')
        gaps.append((participant,missing))
    return {'participants':gaps,'participants_with_gaps':sum(bool(x[1]) for x in gaps)}
