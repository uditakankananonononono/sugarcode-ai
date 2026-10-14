"""Row481 Team Topology Design - Structures for flow.
Supplied-data helper only. Rows (label, kind 0..3 = stream/enabling/complicated/platform, cognitive load 0..10). Return load and team count per kind and sorted labels with load above 7.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a valid topology, delivery flow or external effects.
"""
def _rows(value, name, cap, arity):
    if type(value) not in (list, tuple): raise TypeError(name + ': exact list or tuple required')
    if not 1 <= len(value) <= cap: raise ValueError(name + ': row count outside declared range')
    for row in value:
        if type(row) not in (list, tuple): raise TypeError(name + ': exact list or tuple row required')
        if len(row) != arity: raise ValueError(name + ': wrong row arity')


def _label(value):
    if type(value) is not str: raise TypeError('exact string label required')
    if not 1 <= len(value) <= 24 or not value.isascii() or not all(c.isalnum() or c == '_' for c in value):
        raise ValueError('label must be 1..24 ASCII word characters')


def _integer(value, lo, hi):
    if type(value) is not int: raise TypeError('exact nonbool integer required')
    if not lo <= value <= hi: raise ValueError('integer outside declared range')


def analyze_team_kind_load(rows):
    _rows(rows, 'teams', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 3)
        _integer(row[2], 0, 10)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('team labels must be unique')
    totals=[0,0,0,0]
    counts=[0,0,0,0]
    for row in rows:
        totals[row[1]]+=row[2]
        counts[row[1]]+=1
    return {'kind_load':totals,'kind_teams':counts,'overloaded':sorted(row[0] for row in rows if row[2]>7),'topology_valid':False}
