"""Row 1367, ABS Analysis.

abs_reserve_fixture computes supplied due x minus received y shortfall
floored at zero, then absorbs shortfalls from one shared reserve in label
order. Returns shortfalls (label,gap,covered,uncovered), reserve_left and
uncovered total. Excess received counts do not replenish reserve. No ABS
valuation, credit model, legal contract interpretation or advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
reserve defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, reserve, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: ABS valuation, asset credit model, contract interpretation, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: absorbs supplied shortfall counts with a shared reserve, no ABS analysis'
NOT_CLAIMED = ('ABS valuation', 'asset credit model', 'contract interpretation', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def abs_reserve_fixture(rows, reserve=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(reserve) is not int or not 0 <= reserve <= 10:
        raise ValueError('reserve must be a nonbool integer between 0 and 10')
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
    left=reserve; values=[]
    for n,due,received in sorted(clean,key=lambda r:r[0]):
        gap=max(due-received,0); covered=min(gap,left); left-=covered
        values.append((n,gap,covered,gap-covered))
    return {'shortfalls':values,'reserve_left':left,'uncovered':sum(u for n,g,c,u in values)}
