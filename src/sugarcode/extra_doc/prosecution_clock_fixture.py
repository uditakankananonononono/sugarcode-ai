"""Row 1231, Patent Prosecution.

prosecution_clock_fixture adds supplied abstract start x and interval y then
subtracts now. Returns sorted remaining clocks, expired negative labels,
today zero labels and next as minimum nonnegative clock or None. No official
patent deadline is verified and no filing or prosecution action is taken.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
now defaults to 5, an exact int from 0 to 20.
Validation order: rows type, rows size, now, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: patent prosecution, official deadlines, legal advice, filing or submission, production readiness.
"""

SCOPE = 'PARTIAL: inventories supplied abstract response clocks, no patent prosecution'
NOT_CLAIMED = ('patent prosecution', 'official deadlines', 'legal advice', 'filing or submission', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def prosecution_clock_fixture(rows, now=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(now) is not int or not 0 <= now <= 20:
        raise ValueError('now must be a nonbool integer between 0 and 20')
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
    clocks=[(n,x+y-now) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'clocks':clocks,'expired':[n for n,v in clocks if v<0],
            'today':[n for n,v in clocks if v==0],'next':min((v for n,v in clocks if v>=0),default=None)}
