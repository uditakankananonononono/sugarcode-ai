"""Row 1461, Augmented Reality Learning.

ar_overlay_fixture gives supplied marker count x overlays_per_marker
capacity and compares supplied overlay count y. Returns sorted overlays
(label,placed,unplaced,spare), fitted zero-unplaced labels, unplaced and
spare totals. No AR learning system, actual overlays, spatial registration,
device operation, content validity or learning effectiveness is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
overlays_per_marker defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, overlays_per_marker, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: AR learning system, spatial registration, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied marker/overlay count capacity accounting, no AR learning system'
NOT_CLAIMED = ('AR learning system', 'spatial registration', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ar_overlay_fixture(rows, overlays_per_marker=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(overlays_per_marker) is not int or not 1 <= overlays_per_marker <= 5:
        raise ValueError('overlays_per_marker must be a nonbool integer between 1 and 5')
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
    values=sorted((n,min(overlays_per_marker*x,y),max(y-overlays_per_marker*x,0),max(overlays_per_marker*x-y,0)) for n,x,y in clean)
    return {'overlays':values,'fitted':[n for n,a,u,s in values if u==0],
            'unplaced':sum(u for n,a,u,s in values),'spare':sum(s for n,a,u,s in values)}
