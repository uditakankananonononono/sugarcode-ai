"""Row 1412, Momentum.

momentum_change_fixture computes supplied abstract end y minus start x
relative to positive start x. Returns sorted changes Fraction strings or
None for zero start, rising meeting nonnegative percent threshold and
undefined labels. No actual financial momentum signal, time-series market
data, market prediction, strategy backtest or financial advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
threshold defaults to 20, an exact int from 0 to 100.
Validation order: rows type, rows size, threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: financial momentum signal, market prediction, strategy backtest, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied end/start relative-count change rank, no financial momentum signal'
NOT_CLAIMED = ('financial momentum signal', 'market prediction', 'strategy backtest', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def momentum_change_fixture(rows, threshold=20):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(threshold) is not int or not 0 <= threshold <= 100:
        raise ValueError('threshold must be a nonbool integer between 0 and 100')
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
    values=sorted((n,F(y-x,x) if x else None) for n,x,y in clean)
    return {'changes':[(n,str(v)) if v is not None else (n,None) for n,v in values],
            'rising':[n for n,v in values if v is not None and v>=F(threshold,100)],
            'undefined':[n for n,v in values if v is None]}
