"""Row 1462, Mixed Reality Learning.

mr_balance_fixture pairs supplied physical x and virtual y abstract
counts by minimum and computes signed difference. Returns sorted pairs
(label,paired,difference), balanced inclusive absolute tolerance,
physical_heavy above positive tolerance and virtual_heavy below negative.
No MR learning system, spatial registration, actual content/device operation
or learning effectiveness is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tolerance defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, tolerance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: MR learning system, spatial registration, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied physical/virtual count pairing at balance tolerance, no MR learning system'
NOT_CLAIMED = ('MR learning system', 'spatial registration', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def mr_balance_fixture(rows, tolerance=2):
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
    values=sorted((n,min(x,y),x-y) for n,x,y in clean)
    return {'pairs':values,'balanced':[n for n,p,d in values if abs(d)<=tolerance],
            'physical_heavy':[n for n,p,d in values if d>tolerance],
            'virtual_heavy':[n for n,p,d in values if d<-tolerance]}
