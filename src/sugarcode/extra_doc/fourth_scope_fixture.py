"""Row 1271, Fourth Amendment.

fourth_scope_fixture normalizes abstract supplied endpoints into closed
index intervals. Returns sorted intervals, inside labels containing index,
and distance (label,nonnegative distance to nearest interval point). No
search, seizure, warrant, legal authority or constitutional test is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
index defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, index, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: Fourth Amendment, search legality, legal authority, constitutional rights, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied authorization-window counts, no Fourth Amendment analysis'
NOT_CLAIMED = ('Fourth Amendment', 'search legality', 'legal authority', 'constitutional rights', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def fourth_scope_fixture(rows, index=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(index) is not int or not 0 <= index <= 10:
        raise ValueError('index must be a nonbool integer between 0 and 10')
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
    intervals=[(n,min(x,y),max(x,y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'intervals':intervals,'inside':[n for n,a,b in intervals if a<=index<=b],
            'distance':[(n,max(a-index,0,index-b)) for n,a,b in intervals]}
