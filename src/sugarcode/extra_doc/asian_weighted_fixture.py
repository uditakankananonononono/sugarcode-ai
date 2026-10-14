"""Row 1371, Asian Options.

asian_weighted_fixture weights abstract observation x by count y and
computes positive weighted-average excess above strike. Returns average and
payoff Fraction strings or None for zero weight, weight and defined flag.
No real Asian option pricing, market path, discounting, stochastic simulation
or investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
strike defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, strike, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: Asian option pricing, market path, stochastic simulation, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied count-weighted average excess, no Asian option pricing'
NOT_CLAIMED = ('Asian option pricing', 'market path', 'stochastic simulation', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def asian_weighted_fixture(rows, strike=3):
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
    weight=sum(y for n,x,y in clean)
    average=F(sum(x*y for n,x,y in clean),weight) if weight else None
    return {'average':str(average) if average is not None else None,
            'payoff':str(max(average-strike,F(0))) if average is not None else None,
            'weight':weight,'defined':bool(weight)}
