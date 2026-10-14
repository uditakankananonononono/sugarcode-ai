"""Row 755: Devil's Advocacy - Argues against.

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


def rank_supplied_counterpoints(rows):
    """Rows: (counterpoint_id, supporting_fact_count, assumption_count,
    unresolved_objection_count). Fixed challenge priority: more objections,
    then more supporting facts, then fewer assumptions, tie ID. No counterargument
    generation, fact checking, persuasion or actual advocacy. Supplied rubric.
    """
    _rows(rows, 4)
    for point,facts,assumptions,objections in rows:
        _label(point)
        _integer(facts, 0, 100)
        _integer(assumptions, 0, 100)
        _integer(objections, 0, 100)
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate counterpoint')
    ranked=sorted(rows,key=lambda x:(-x[3],-x[1],x[2],x[0]))
    return {'ranked':[x[0] for x in ranked],'first_to_review':ranked[0][0]}
