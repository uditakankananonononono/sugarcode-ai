"""Row 1369, Exotic Options.

exotic_average_fixture treats both x and y in each row as equally weighted
abstract observations and computes their arithmetic mean and positive excess
above strike. Returns average and payoff Fraction strings, in_money strictly
above strike and observations count. No actual exotic-option pricing,
stochastic path, discounting, contract valuation or advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
strike defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, strike, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: exotic option pricing, stochastic path, contract valuation, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: computes positive arithmetic-average count excess, no exotic-option pricing'
NOT_CLAIMED = ('exotic option pricing', 'stochastic path', 'contract valuation', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def exotic_average_fixture(rows, strike=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(strike) is not int or not 0 <= strike <= 10:
        raise ValueError('strike must be a nonbool integer between 0 and 10')
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
    average=F(sum(x+y for n,x,y in clean),2*len(clean))
    payoff=max(average-strike,F(0))
    return {'average':str(average),'payoff':str(payoff),'in_money':average>strike,'observations':2*len(clean)}
