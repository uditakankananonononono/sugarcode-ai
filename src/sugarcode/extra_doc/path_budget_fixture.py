"""Row 1475, Path Recommendation.

path_budget_fixture chooses a subset of supplied benefit x and cost y
counts within budget. Maximizes benefit, then minimizes cost, then label
tuple lexicographically. Empty subset allowed; output selected is a list,
benefit/cost/remaining integer counts. No actual learning-path recommendation,
prerequisite inference, content sequencing or learning effectiveness.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
budget defaults to 7, an exact int from 0 to 20.
Validation order: rows type, rows size, budget, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: learning path recommendation, prerequisite inference, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied benefit/cost count subset choice, no learning-path recommendation'
NOT_CLAIMED = ('learning path recommendation', 'prerequisite inference', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def path_budget_fixture(rows, budget=7):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(budget) is not int or not 0 <= budget <= 20:
        raise ValueError('budget must be a nonbool integer between 0 and 20')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 0 and 10')
        if type(y) is not int or not 0 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 0 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from itertools import combinations
    candidates=[]
    ordered=sorted(clean,key=lambda r:r[0])
    for size in range(len(ordered)+1):
        for subset in combinations(ordered,size):
            cost=sum(y for n,x,y in subset); benefit=sum(x for n,x,y in subset)
            if cost<=budget: candidates.append((benefit,cost,tuple(n for n,x,y in subset)))
    benefit,cost,names=min(candidates,key=lambda r:(-r[0],r[1],r[2]))
    return {'selected':list(names),'benefit':benefit,'cost':cost,'remaining':budget-cost}
