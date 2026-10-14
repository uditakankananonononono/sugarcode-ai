"""Row 1383, FX Trading.

fx_rate_fixture converts supplied source count x at tenths per unit and
subtracts supplied target obligation y. Returns sorted net Fraction strings,
positive labels and total. The fixture rate is supplied, not a live exchange
rate; no FX trading, trade execution, bid/ask spread, fees, settlement,
actual currency exchange or investment advice is implemented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tenths defaults to 12, an exact int from 1 to 20.
Validation order: rows type, rows size, tenths, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: FX trading, live exchange rates, trade execution, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied count conversion at positive rational fixture rate, no FX trading'
NOT_CLAIMED = ('FX trading', 'live exchange rates', 'trade execution', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def fx_rate_fixture(rows, tenths=12):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(tenths) is not int or not 1 <= tenths <= 20:
        raise ValueError('tenths must be a nonbool integer between 1 and 20')
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
    values=sorted((n,F(x*tenths,10)-y) for n,x,y in clean)
    return {'net':[(n,str(v)) for n,v in values],'positive':[n for n,v in values if v>0],
            'total':str(sum((v for n,v in values),F(0)))}
