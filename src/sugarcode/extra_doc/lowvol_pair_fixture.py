"""Row 1416, Low Volatility.

lowvol_pair_fixture computes population variance of each supplied pair
of abstract counts x and y, squared difference divided by four. Returns
sorted variances Fraction strings, low at most ceiling, high above and
maximum Fraction string. No financial volatility estimate, time-series
analysis, market risk prediction or financial advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
ceiling defaults to 4, an exact int from 0 to 25.
Validation order: rows type, rows size, ceiling, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: financial volatility estimate, time series analysis, risk prediction, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied two-count population variance ceiling, no financial volatility estimate'
NOT_CLAIMED = ('financial volatility estimate', 'time series analysis', 'risk prediction', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def lowvol_pair_fixture(rows, ceiling=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(ceiling) is not int or not 0 <= ceiling <= 25:
        raise ValueError('ceiling must be a nonbool integer between 0 and 25')
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
    values=sorted((n,F((x-y)**2,4)) for n,x,y in clean)
    return {'variances':[(n,str(v)) for n,v in values],'low':[n for n,v in values if v<=ceiling],
            'high':[n for n,v in values if v>ceiling],'maximum':str(max(v for n,v in values))}
