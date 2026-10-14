"""Row 1453, Distance Education.

distance_packet_fixture subtracts supplied delivered packet count y from
required x, floors missing at zero and assigns retry attempts as retry times
missing. Returns sorted missing (label,missing,retry_attempts), complete,
retry_attempts total and packets total. No distance education delivery,
learning effectiveness, delivery verification or external communication.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
retry defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, retry, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: distance education delivery, learning effectiveness, delivery verification, production readiness.
"""

SCOPE = 'PARTIAL: supplied packet/delivery count retry accounting, no distance education delivery'
NOT_CLAIMED = ('distance education delivery', 'learning effectiveness', 'delivery verification', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def distance_packet_fixture(rows, retry=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(retry) is not int or not 0 <= retry <= 5:
        raise ValueError('retry must be a nonbool integer between 0 and 5')
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
    values=sorted((n,max(x-y,0),retry*max(x-y,0)) for n,x,y in clean)
    return {'missing':values,'complete':[n for n,m,r in values if m==0],
            'retry_attempts':sum(r for n,m,r in values),'packets':sum(x for n,x,y in clean)}
