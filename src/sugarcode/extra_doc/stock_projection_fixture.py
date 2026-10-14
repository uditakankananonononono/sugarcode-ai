"""Row 1155, Medication Management.

stock_projection_fixture subtracts periods*y supplied abstract consumption
from supplied stock x. Returns label-sorted stocks (label,signed_balance),
shortages (label,positive_shortfall) for negative balances and exhausted for
exact zero. No medication names, doses or regimens are interpreted.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
periods defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, periods, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: medication management, dose or regimen, drug safety, clinical advice, production readiness.
"""

SCOPE = 'PARTIAL: projects abstract supplied stock consumption, no medication management'
NOT_CLAIMED = ('medication management', 'dose or regimen', 'drug safety', 'clinical advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def stock_projection_fixture(rows, periods=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(periods) is not int or not 0 <= periods <= 10:
        raise ValueError('periods must be a nonbool integer between 0 and 10')
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
    stocks = [(n, stock - periods * use) for n, stock, use in sorted(clean,key=lambda r:r[0])]
    return {'stocks':stocks,'shortages':[(n,-v) for n,v in stocks if v<0],
            'exhausted':[n for n,v in stocks if v==0]}
