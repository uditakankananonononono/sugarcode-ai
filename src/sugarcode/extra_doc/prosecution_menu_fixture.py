"""Row 1266, Prosecution Strategy.

prosecution_menu_fixture filters opaque supplied cost x at or below budget
and ranks eligible abstract count y descending then label. Returns eligible
pairs, best all maximum-count labels or empty and excluded labels. No charge,
case merits, evidence, legal strategy or prosecutorial action is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
budget defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, budget, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: prosecution strategy, legal merit, charging decision, external action, production readiness.
"""

SCOPE = 'PARTIAL: filters abstract supplied cost/count menu, no prosecution strategy'
NOT_CLAIMED = ('prosecution strategy', 'legal merit', 'charging decision', 'external action', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def prosecution_menu_fixture(rows, budget=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(budget) is not int or not 0 <= budget <= 10:
        raise ValueError('budget must be a nonbool integer between 0 and 10')
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
    eligible=[(n,y) for n,x,y in clean if x<=budget]
    eligible.sort(key=lambda r:(-r[1],r[0]))
    return {'eligible':eligible,'best':[n for n,v in eligible if v==eligible[0][1]] if eligible else [],
            'excluded':sorted(n for n,x,y in clean if x>budget)}
