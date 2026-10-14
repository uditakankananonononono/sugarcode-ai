"""Row 779: Integrity - Acts consistently.

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


def compare_declared_actions(rows):
    """Rows: (commitment_id, stated_action_code0..2, observed_action_code0..2).
    Compare supplied codes for consistency, report exact match fraction. No
    character/integrity assessment, observation verification, motive inference
    or guarantee of consistent behavior. Fixed caller-data comparison only.
    """
    _rows(rows, 3)
    for commitment,stated,observed in rows:
        _label(commitment)
        _integer(stated, 0, 2)
        _integer(observed, 0, 2)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate commitment')
    mismatches=sorted(c for c,stated,observed in rows if stated!=observed)
    from fractions import Fraction as F
    matched=len(rows)-len(mismatches)
    return {'mismatches':mismatches,'matching_count':matched,
            'match_fraction':str(F(matched,len(rows)))}
