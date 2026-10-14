"""Row 1326, Real Options Analysis.

option_intrinsic_fixture computes scaled abstract positive difference x-y
and y-x for caller-supplied counts. Returns sorted values (label,up,down),
total_up, total_down and equal zero-in-both labels. No time value, stochastic
process, volatility, actual real-option valuation or investment advice is given.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
scale defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, scale, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: real options valuation, time value, stochastic model, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: computes supplied abstract intrinsic value counts, no real options valuation'
NOT_CLAIMED = ('real options valuation', 'time value', 'stochastic model', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def option_intrinsic_fixture(rows, scale=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(scale) is not int or not 1 <= scale <= 5:
        raise ValueError('scale must be a nonbool integer between 1 and 5')
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
    values=[(n,scale*max(0,x-y),scale*max(0,y-x)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'values':values,'total_up':sum(a for n,a,b in values),'total_down':sum(b for n,a,b in values),
            'equal':[n for n,a,b in values if a==0 and b==0]}
