"""Row 753: Principle of Charity - Interprets favorably.

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


def select_fact_compatible_reading(rows):
    """Rows: (reading_id, supplied_contradiction_count, explained_fact_count,
    added_assumption_count). Exclude contradictory readings, prefer greatest
    explained facts then fewest added assumptions then ID. No semantic reading,
    charitable inference, truth/intent verification or actual good-faith proof.
    """
    _rows(rows, 4)
    for reading,contradictions,explained,assumptions in rows:
        _label(reading)
        _integer(contradictions, 0, 100)
        _integer(explained, 0, 100)
        _integer(assumptions, 0, 100)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate reading')
    candidates=sorted((x for x in rows if x[1]==0),key=lambda x:(-x[2],x[3],x[0]))
    return {'ranked':[x[0] for x in candidates],'selected':candidates[0][0] if candidates else None,
            'excluded':sorted(x[0] for x in rows if x[1]>0)}
