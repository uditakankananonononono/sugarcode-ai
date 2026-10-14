"""Row 1296, Oral Argument.

argument_turn_fixture alternates abstract first/second count tokens across
turns with first at even zero-based positions, each capped by supplied x/y.
No missed slot is reassigned. Returns sorted allocations, unused count pairs
and total_used. No speech, advocacy or court timing rule is created or assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
turns defaults to 5, an exact int from 0 to 20.
Validation order: rows type, rows size, turns, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: oral argument, legal advocacy, court timing rules, actual speech, production readiness.
"""

SCOPE = 'PARTIAL: allocates abstract supplied speaking count tokens, no oral argument'
NOT_CLAIMED = ('oral argument', 'legal advocacy', 'court timing rules', 'actual speech', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def argument_turn_fixture(rows, turns=5):
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
    allocations=[(n,min(x,(turns+1)//2),min(y,turns//2)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'allocations':allocations,'unused':[(n,turns-a-b) for n,a,b in allocations],
            'total_used':sum(a+b for n,a,b in allocations)}
