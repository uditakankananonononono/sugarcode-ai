"""Row 1546, Statistical Process Control.

process_range_fixture computes absolute differences of paired supplied
x,y reading counts and flags ranges strictly greater than limit. Returns
sorted ranges, flags, total and maximum. No statistical control inference,
control limits estimation, process stability claim, physical units,
real measurement validation or process certification is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
limit defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, limit, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: statistical control inference, control limits estimation, process stability, physical units, production readiness.
"""

SCOPE = 'PARTIAL: supplied paired reading count range flags, no statistical control inference'
NOT_CLAIMED = ('statistical control inference', 'control limits estimation', 'process stability', 'physical units', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def process_range_fixture(rows, limit=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(limit) is not int or not 0 <= limit <= 10:
        raise ValueError('limit must be a nonbool integer between 0 and 10')
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
    ranges=sorted((n,abs(x-y)) for n,x,y in clean)
    return {'ranges':ranges,'flags':[n for n,v in ranges if v>limit],
            'total':sum(v for n,v in ranges),'maximum':max(v for n,v in ranges)}
