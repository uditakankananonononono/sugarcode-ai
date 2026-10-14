"""Row 1387, Interest Rate Parity.

interestparity_ratio_fixture applies the abstract identity spot times
one plus domestic x in tenths divided by one plus foreign y in tenths.
Returns sorted forwards Fraction strings, premium above spot labels, flat
labels equal spot and spot. No actual interest-rate parity determination,
market data, arbitrage execution, FX forecast or advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
spot defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, spot, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: market parity determination, exchange forecast, arbitrage execution, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied count forward-ratio identity, no market parity determination'
NOT_CLAIMED = ('market parity determination', 'exchange forecast', 'arbitrage execution', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def interestparity_ratio_fixture(rows, spot=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(spot) is not int or not 1 <= spot <= 5:
        raise ValueError('spot must be a nonbool integer between 1 and 5')
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
    values=sorted((n,F(spot*(10+x),10+y)) for n,x,y in clean)
    return {'forwards':[(n,str(v)) for n,v in values],'premium':[n for n,v in values if v>spot],
            'flat':[n for n,v in values if v==spot],'spot':spot}
