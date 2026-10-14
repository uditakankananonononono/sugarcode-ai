"""Row 771: Team Building - Develops cohesion.

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


def summarize_pair_participation(rows):
    """Rows: (member_a, member_b, supplied_shared_activity_count).
    Undirected pair counts; labels distinct, reversed duplicate pairs refused.
    Report per-member total declared shared activities and zero-count pairs.
    No actual team cohesion measurement/activity execution or social inference.
    """
    _rows(rows, 3)
    for a,b,count in rows:
        _label(a)
        _label(b)
        _integer(count, 0, 100)
        if a==b:
            raise ValueError('pair members must differ')
    pairs=[tuple(sorted((a,b))) for a,b,_ in rows]
    if len(set(pairs))!=len(rows):
        raise ValueError('duplicate member pair')
    totals={}
    for a,b,count in rows:
        totals[a]=totals.get(a,0)+count
        totals[b]=totals.get(b,0)+count
    return {'member_totals':sorted(totals.items()),
            'zero_activity_pairs':sorted(tuple(sorted((a,b))) for a,b,c in rows if c==0)}
