"""Row 1254, Probate.

probate_queue_fixture subtracts abstract expense y and fee from supplied
units x. Returns signed balances ascending then label, negative/nonnegative
labels and total. No legal creditor priority, asset value, probate process
or court filing is determined or executed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
fee defaults to 1, an exact int from 0 to 10.
Validation order: rows type, rows size, fee, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: probate administration, legal priority, asset valuation, court filing, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied ledger completion order, no probate administration'
NOT_CLAIMED = ('probate administration', 'legal priority', 'asset valuation', 'court filing', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def probate_queue_fixture(rows, fee=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(fee) is not int or not 0 <= fee <= 10:
        raise ValueError('fee must be a nonbool integer between 0 and 10')
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
    balances=[(n,x-y-fee) for n,x,y in clean]
    balances.sort(key=lambda r:(r[1],r[0]))
    return {'balances':balances,'negative':[n for n,v in balances if v<0],
            'nonnegative':[n for n,v in balances if v>=0],'total':sum(v for n,v in balances)}
