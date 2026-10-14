"""Row 526: Authorization Design - Controls access.

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


def evaluate_access(rows):
    """Rows: (subject, resource, action, grant_bit, explicit_deny_bit).
    Pure deny-overrides decision over supplied assertions. No live permissions,
    identity lookup, enforcement or authorization service integration.
    """
    _rows(rows, 5)
    for subject, resource, action, grant, deny in rows:
        for value in (subject, resource, action):
            _label(value)
        _integer(grant, 0, 1)
        _integer(deny, 0, 1)
    if len({(x[0],x[1],x[2]) for x in rows}) != len(rows):
        raise ValueError('duplicate request')
    return {'decisions': [(subject,resource,action,grant==1 and deny==0)
                          for subject,resource,action,grant,deny in sorted(rows)]}
