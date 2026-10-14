"""Row 592: Differential Privacy - Protects individuals.

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


def compose_budgets(rows):
    """Rows: (mechanism_id, epsilon_numerator, epsilon_denominator,
    delta_numerator, delta_denominator). Return exact sequential composition
    upper bounds by summing declared epsilon/delta (delta capped at 1).
    This accounts caller claims ONLY: no DP mechanism, sensitivity calibration,
    randomness, neighboring-data proof or actual individual protection.
    """
    _rows(rows, 5)
    for mechanism, en, ed, dn, dd in rows:
        _label(mechanism)
        _integer(en, 0, 1000)
        _integer(ed, 1, 1000)
        _integer(dn, 0, 1000000)
        _integer(dd, 1, 1000000)
        if dn>dd:
            raise ValueError('delta fraction must be at most one')
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate mechanism')
    from fractions import Fraction as F
    epsilon=sum((F(en,ed) for _,en,ed,_,_ in rows),F(0))
    delta=min(F(1),sum((F(dn,dd) for _,_,_,dn,dd in rows),F(0)))
    return {'epsilon_bound_fraction':str(epsilon),'delta_bound_fraction':str(delta),
            'mechanisms':len(rows)}
