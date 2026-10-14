"""Row 1513, Special Education.

special_support_fixture gives supplied staff count y capacity for
sessions_per_staff sessions and compares requested session count x. Returns
sorted sessions (label,assigned,unassigned), covered zero-gap labels, assigned
and unassigned totals. No special-education needs assessment, diagnosis,
actual staffing, accommodation recommendation or care provision is given.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
sessions_per_staff defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, sessions_per_staff, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: special education needs assessment, diagnosis, accommodation recommendation, production readiness.
"""

SCOPE = 'PARTIAL: supplied session/staff count capacity gaps, no special-education needs assessment'
NOT_CLAIMED = ('special education needs assessment', 'diagnosis', 'accommodation recommendation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def special_support_fixture(rows, sessions_per_staff=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(sessions_per_staff) is not int or not 1 <= sessions_per_staff <= 5:
        raise ValueError('sessions_per_staff must be a nonbool integer between 1 and 5')
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
    values=sorted((n,min(x,sessions_per_staff*y),max(x-sessions_per_staff*y,0)) for n,x,y in clean)
    return {'sessions':values,'covered':[n for n,a,g in values if g==0],
            'assigned':sum(a for n,a,g in values),'unassigned':sum(g for n,a,g in values)}
