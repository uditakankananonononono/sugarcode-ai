"""Row 1372, Lookback Options.

lookback_extrema_fixture computes global extrema over both supplied
abstract observation counts x and y. Returns high, low, range, positive
high-minus-strike call and strike-minus-low put counts, and high_labels
containing at least one maximum. No actual option valuation, continuous
monitoring, market path, discounting or investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
strike defaults to 4, an exact int from 0 to 10.
Validation order: rows type, rows size, strike, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: lookback option valuation, continuous monitoring, market path, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied count extrema range and strike excess, no lookback option valuation'
NOT_CLAIMED = ('lookback option valuation', 'continuous monitoring', 'market path', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def lookback_extrema_fixture(rows, strike=4):
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
    values=[v for n,x,y in clean for v in (x,y)]
    high=max(values); low=min(values)
    return {'high':high,'low':low,'range':high-low,'call':max(high-strike,0),
            'put':max(strike-low,0),'high_labels':sorted(n for n,x,y in clean if max(x,y)==high)}
