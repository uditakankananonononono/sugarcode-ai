"""Row 778: Ethics - Does right.

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


def review_declared_ethical_checks(rows):
    """Rows: (decision_id, required_permission_confirmed_bit,
    harm_review_done_bit, conflict_disclosed_bit). Fixed missing-check checklist.
    No moral judgment, doing right, permission validation or absence-of-harm
    proof; all flags caller assertions, no actual actions taken.
    """
    _rows(rows, 4)
    for decision,permission,harm,conflict in rows:
        _label(decision)
        _integer(permission, 0, 1)
        _integer(harm, 0, 1)
        _integer(conflict, 0, 1)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate decision')
    decisions=[]
    for decision,permission,harm,conflict in sorted(rows):
        missing=[]
        if permission==0:
            missing.append('permission_confirmation')
        if harm==0:
            missing.append('harm_review')
        if conflict==0:
            missing.append('conflict_disclosure')
        decisions.append((decision,missing))
    return {'decisions':decisions,'decisions_with_gaps':sum(bool(x[1]) for x in decisions)}
