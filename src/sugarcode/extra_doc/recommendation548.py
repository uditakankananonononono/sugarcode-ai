"""Row 548: Recommendation System - Suggests items.

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


def recommend_items(rows):
    """Rows: (item_id, preference_weight, supplied_affinity).
    Rank all supplied candidates by exact integer weight*affinity descending,
    ties by item identifier. No learned preference, personalization, retrieval,
    collaborative filtering or external recommendation action.
    """
    _rows(rows, 3)
    for item, weight, affinity in rows:
        _label(item)
        _integer(weight, -1000, 1000)
        _integer(affinity, -1000, 1000)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate item')
    ranked = sorted(((item,weight*affinity) for item,weight,affinity in rows),key=lambda x:(-x[1],x[0]))
    return {'recommendations': ranked}
