"""Row 1352, Volatility Modeling.

volatility_square_fixture forms abstract x minus y differences and scales
them by scale. Returns population variance and mean as Fraction strings,
constant for zero variance and count. It returns squared deviation, not
standard deviation; no market series, forecasting, annualization or advice.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
scale defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, scale, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: volatility forecasting, market returns, annualization, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: computes population squared deviation of count fixtures, no volatility forecast'
NOT_CLAIMED = ('volatility forecasting', 'market returns', 'annualization', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def volatility_square_fixture(rows, scale=2):
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
    from fractions import Fraction as F
    values=[x-y for n,x,y in clean]
    count=len(values); total=sum(values)
    variance=F(scale*scale*(count*sum(v*v for v in values)-total*total),count*count)
    return {'variance':str(variance),'mean':str(F(scale*total,count)),
            'constant':variance==0,'count':count}
