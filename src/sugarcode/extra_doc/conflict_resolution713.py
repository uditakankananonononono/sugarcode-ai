"""Row 713: Conflict Resolution - Resolves disputes.

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


def find_common_interval(rows):
    """Rows: (party_id, acceptable_lower_integer, acceptable_upper_integer).
    Intersect supplied one-dimensional acceptance intervals. Return exact
    midpoint compromise if feasible else gap. No actual dispute understanding,
    negotiation, agreement, interpersonal conflict resolution or fairness proof.
    Caller intervals are assertions, not verified consent to a final proposal.
    """
    _rows(rows, 3)
    for party,low,high in rows:
        _label(party)
        _integer(low, -1000000, 1000000)
        _integer(high, -1000000, 1000000)
        if low>high:
            raise ValueError('reversed acceptance interval')
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate party')
    low=max(x[1] for x in rows)
    high=min(x[2] for x in rows)
    from fractions import Fraction as F
    feasible=low<=high
    return {'feasible':feasible,'common_interval':(low,high) if feasible else None,
            'proposal_fraction':str(F(low+high,2)) if feasible else None,
            'gap':0 if feasible else low-high}
