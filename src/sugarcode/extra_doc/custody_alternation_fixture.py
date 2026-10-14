"""Row 1250, Child Custody.

custody_alternation_fixture alternates abstract counters first/second for
turns slots, first at even zero-based slots, each capped by supplied x/y.
Unfilled slots are not reassigned. Returns sorted allocations (label,first,
second,unfilled), complete zero-gap labels and total unused. No child's needs,
family arrangement, legal custody or actual schedule is assessed or created.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
turns defaults to 5, an exact int from 0 to 20.
Validation order: rows type, rows size, turns, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: child custody, best interests assessment, legal schedule, real family arrangement, production readiness.
"""

SCOPE = 'PARTIAL: alternates abstract supplied counters, no child custody planning'
NOT_CLAIMED = ('child custody', 'best interests assessment', 'legal schedule', 'real family arrangement', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def custody_alternation_fixture(rows, turns=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(turns) is not int or not 0 <= turns <= 20:
        raise ValueError('turns must be a nonbool integer between 0 and 20')
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
    allocations=[]
    for n,x,y in sorted(clean,key=lambda r:r[0]):
        a=min(x,(turns+1)//2); b=min(y,turns//2)
        allocations.append((n,a,b,turns-a-b))
    return {'allocations':allocations,'complete':[n for n,a,b,g in allocations if g==0],
            'unused':sum(g for n,a,b,g in allocations)}
