"""Row 1327, Cost of Capital.

capital_cost_fixture treats supplied x as abstract rate-count and y as
positive weight. Adds spread to each rate and the weighted mean. Returns
sorted rates, mean Fraction string, total weight and above-mean labels.
No real market rate, financing cost, risk or financial advice is estimated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
spread defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, spread, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: real cost of capital, market data, risk estimation, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: scales supplied positive weighted rate-count mean, no capital cost estimate'
NOT_CLAIMED = ('real cost of capital', 'market data', 'risk estimation', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def capital_cost_fixture(rows, spread=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(spread) is not int or not 0 <= spread <= 10:
        raise ValueError('spread must be a nonbool integer between 0 and 10')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 1 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 1 and 10')
        if type(y) is not int or not 1 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 1 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    weight=sum(y for n,x,y in clean)
    base=F(sum(x*y for n,x,y in clean),weight)
    rates=[(n,x+spread) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'rates':rates,'mean':str(base+spread),'weight':weight,
            'above':[n for n,v in rates if v>base+spread]}
