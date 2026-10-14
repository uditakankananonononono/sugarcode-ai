"""Row 642, Cost Optimization: cheapest-pain subset to cut for a savings target.

Items are (name, monthly_cost, impact). Cutting an item saves its cost and incurs
its impact. Find the subset whose savings reach the target with the least total
impact; ties go to fewer items, then to the lexicographically smallest tuple of
input indexes. Exhaustive over all subsets (at most 12 items). If even cutting
everything misses the target the result is infeasible.
Caps (checked before any work): at most 12 items, unique names of 1 to 16
characters, cost 1 to 100000, impact 1 to 10, target 0 to 1000000, nonbool ints.
NOT_CLAIMED: real prices, discounts, dependencies between items, quality or
revenue effects, recurring savings over time, production readiness.
"""
SCOPE = 'PARTIAL: exhaustive subset search over at most 12 independent items'
NOT_CLAIMED = ('real prices', 'discounts', 'dependencies between items', 'quality or revenue effects',
               'recurring savings over time', 'production readiness')


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def cut_costs(items, target):
    if type(items) not in (list, tuple):
        raise TypeError('items must be a list or tuple')
    if len(items) > 12:
        raise ValueError('items must contain at most 12 entries')
    _int(target, 0, 1000000, 'target must be a nonbool integer between 0 and 1000000')
    for it in items:
        if type(it) not in (list, tuple) or len(it) != 3:
            raise ValueError('each item must be a (name, cost, impact) triple')
        if type(it[0]) is not str or not 1 <= len(it[0]) <= 16:
            raise ValueError('item names must be strings of 1 to 16 characters')
        _int(it[1], 1, 100000, 'cost must be a nonbool integer between 1 and 100000')
        _int(it[2], 1, 10, 'impact must be a nonbool integer between 1 and 10')
    if len({it[0] for it in items}) != len(items):
        raise ValueError('item names must be unique')
    n, best = len(items), None
    for mask in range(1 << n):
        idx = tuple(i for i in range(n) if mask >> i & 1)
        saved = sum(items[i][1] for i in idx)
        if saved < target:
            continue
        key = (sum(items[i][2] for i in idx), len(idx), idx)
        if best is None or key < best[0]:
            best = (key, saved)
    if best is None:
        return {'feasible': False, 'cut': [], 'savings': 0, 'impact': 0}
    (impact, _, idx), saved = best
    return {'feasible': True, 'cut': [items[i][0] for i in idx], 'savings': saved, 'impact': impact}
