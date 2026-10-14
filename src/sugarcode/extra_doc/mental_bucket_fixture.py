"""Row 1404, Mental Accounting.

mental_bucket_fixture adds fixed allowance to supplied bucket resource x
and subtracts spending y independently per row. Returns sorted balances,
separate surplus and deficit totals, net and unfunded negative labels. It
does not transfer resources between buckets. No mental-accounting inference,
bias diagnosis, real financial planning or financial advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
allowance defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, allowance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: mental accounting inference, bias diagnosis, financial planning, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied separate bucket surplus/deficit counts, no mental-accounting inference'
NOT_CLAIMED = ('mental accounting inference', 'bias diagnosis', 'financial planning', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def mental_bucket_fixture(rows, allowance=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(allowance) is not int or not 0 <= allowance <= 5:
        raise ValueError('allowance must be a nonbool integer between 0 and 5')
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
    values=sorted((n,x+allowance-y) for n,x,y in clean)
    surplus=sum(max(v,0) for n,v in values); deficit=sum(max(-v,0) for n,v in values)
    return {'balances':values,'surplus':surplus,'deficit':deficit,'net':surplus-deficit,
            'unfunded':[n for n,v in values if v<0]}
