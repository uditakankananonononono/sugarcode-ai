"""Row 1373, Forward Starting Options.

forwardstart_ratio_fixture treats x as supplied start count and y as
supplied final count, setting a fixture strike at percent of x and taking
positive final excess. Returns sorted payoffs Fraction strings, positive
labels and total. Zero x is permitted by count convention. No actual
forward-start option pricing, market model, contract valuation or advice.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 100, an exact int from 0 to 200.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: forward-start option pricing, market model, contract valuation, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied start/final count ratio-strike excess, no forward-start option pricing'
NOT_CLAIMED = ('forward-start option pricing', 'market model', 'contract valuation', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def forwardstart_ratio_fixture(rows, percent=100):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(percent) is not int or not 0 <= percent <= 200:
        raise ValueError('percent must be a nonbool integer between 0 and 200')
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
    from fractions import Fraction as F
    values=sorted((n,max(F(y)-F(percent*x,100),F(0))) for n,x,y in clean)
    return {'payoffs':[(n,str(v)) for n,v in values],
            'positive':[n for n,v in values if v>0],'total':str(sum((v for n,v in values),F(0)))}
