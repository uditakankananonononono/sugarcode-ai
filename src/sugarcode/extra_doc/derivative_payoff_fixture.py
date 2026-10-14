"""Row 1347, Derivatives Pricing.

derivative_payoff_fixture takes abstract terminal count x minus strike count
y floored at zero, then discounts one period by rate percent. Returns sorted
value Fraction strings, total and zero labels. No probability distribution,
risk-neutral expectation, real derivative price, market data/calibration or
investment advice is modeled.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
rate defaults to 10, an exact int from 0 to 100.
Validation order: rows type, rows size, rate, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: derivative valuation model, risk-neutral probabilities, market calibration, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: discounts supplied abstract terminal payoff counts for one period, no derivative valuation model'
NOT_CLAIMED = ('derivative valuation model', 'risk-neutral probabilities', 'market calibration', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def derivative_payoff_fixture(rows, rate=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(rate) is not int or not 0 <= rate <= 100:
        raise ValueError('rate must be a nonbool integer between 0 and 100')
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
    values=[(n,F(max(0,x-y)*100,100+rate)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'values':[(n,str(v)) for n,v in values],'total':str(sum((v for n,v in values),F(0))),
            'zero':[n for n,v in values if v==0]}
