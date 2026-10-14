"""Row 1409, Market Efficiency.

market_error_fixture computes absolute count differences between supplied
prediction x and observation y. Returns sorted errors, within inclusive
tolerance, total_error and maximum. No actual price data, market-efficiency
conclusion, statistical hypothesis test, causal claim, price prediction,
strategy evaluation or financial advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tolerance defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, tolerance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: market efficiency conclusion, statistical hypothesis test, price prediction, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied prediction/observation absolute-error counts, no market-efficiency conclusion'
NOT_CLAIMED = ('market efficiency conclusion', 'statistical hypothesis test', 'price prediction', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def market_error_fixture(rows, tolerance=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(tolerance) is not int or not 0 <= tolerance <= 10:
        raise ValueError('tolerance must be a nonbool integer between 0 and 10')
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
    values=sorted((n,abs(x-y)) for n,x,y in clean)
    return {'errors':values,'within':[n for n,v in values if v<=tolerance],
            'total_error':sum(v for n,v in values),'maximum':max(v for n,v in values)}
