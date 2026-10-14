"""Row 751: Steelmanning - Strengthens opposing views.

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


def rank_supplied_arguments(rows):
    """Rows: (argument_id, supplied_premise_count, supported_premise_count,
    relevance_weight). Rank supplied arguments by exact supported share times
    relevance, tie ID. No argument generation/strengthening/truth verification,
    rhetoric evaluation or actual steelmanning. Zero-premise rows refused.
    """
    _rows(rows, 4)
    for argument,total,supported,weight in rows:
        _label(argument)
        _integer(total, 0, 100)
        _integer(supported, 0, 100)
        _integer(weight, 1, 10)
        if total==0:
            raise ValueError('argument needs at least one premise')
        if supported>total:
            raise ValueError('supported premises exceed total')
    if len({x[0] for x in rows})!=len(rows):
        raise ValueError('duplicate argument')
    from fractions import Fraction as F
    scored=[(argument,F(supported,total)*weight) for argument,total,supported,weight in rows]
    ranked=sorted(scored,key=lambda x:(-x[1],x[0]))
    return {'ranked':[(a,str(score)) for a,score in ranked],'selected':ranked[0][0]}
