"""Row 1597, Smart Grid.

smart_grid_transfer_fixture pools positive and negative supplied
generation x minus load y count balances and transfers the smaller pool
up to capacity. Returns sorted balances, transferred count, unserved
deficit and unused surplus. No smart grid control, physical dispatch,
grid stability, real network constraints or engineering safety.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
capacity defaults to 4, an exact int from 0 to 10.
Validation order: rows type, rows size, capacity, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: smart grid control, physical dispatch, grid stability, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied generation/load count pool transfer, no smart grid control'
NOT_CLAIMED = ('smart grid control', 'physical dispatch', 'grid stability', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def smart_grid_transfer_fixture(rows, capacity=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(capacity) is not int or not 0 <= capacity <= 10:
        raise ValueError('capacity must be a nonbool integer between 0 and 10')
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
    balances=sorted((n,x-y) for n,x,y in clean)
    surplus=sum(max(0,v) for n,v in balances)
    deficit=sum(max(0,-v) for n,v in balances)
    transfer=min(surplus,deficit,capacity)
    return {'balances':balances,'transferred':transfer,'unserved':deficit-transfer,'unused':surplus-transfer}
