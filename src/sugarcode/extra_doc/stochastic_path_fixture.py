"""Row 1354, Stochastic Volatility.

stochastic_path_fixture accumulates supplied abstract up x minus down y
counts in label order, floors each running value at zero and starts at initial.
Returns path, final, zero labels and minimum including initial. It generates
no randomness and has no stochastic process, market calibration, actual
volatility, uncertainty estimate or investment advice.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
initial defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, initial, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: stochastic volatility simulation, random process, market calibration, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: accumulates supplied abstract variance increments, no stochastic volatility simulation'
NOT_CLAIMED = ('stochastic volatility simulation', 'random process', 'market calibration', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def stochastic_path_fixture(rows, initial=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(initial) is not int or not 0 <= initial <= 10:
        raise ValueError('initial must be a nonbool integer between 0 and 10')
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
    path=[]; value=initial
    for n,up,down in sorted(clean,key=lambda r:r[0]):
        value=max(0,value+up-down)
        path.append((n,value))
    return {'path':path,'final':value,'zero':[n for n,v in path if v==0],
            'minimum':min([initial]+[v for n,v in path])}
