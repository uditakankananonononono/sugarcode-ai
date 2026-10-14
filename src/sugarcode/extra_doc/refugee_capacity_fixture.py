"""Row 1247, Refugee Law.

refugee_capacity_fixture reserves abstract units from supplied capacity y,
floors available at zero and assigns min(request x,available). Returns sorted
available, assigned and missing count pairs. It determines no refugee legal
status, eligibility or real resource allocation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
reserve defaults to 1, an exact int from 0 to 10.
Validation order: rows type, rows size, reserve, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: refugee law, legal status, eligibility, real resource assignment, production readiness.
"""

SCOPE = 'PARTIAL: compares abstract supplied resource tallies, no refugee law analysis'
NOT_CLAIMED = ('refugee law', 'legal status', 'eligibility', 'real resource assignment', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def refugee_capacity_fixture(rows, reserve=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(reserve) is not int or not 0 <= reserve <= 10:
        raise ValueError('reserve must be a nonbool integer between 0 and 10')
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
    available=[(n,max(0,y-reserve)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    assigned=[(n,min(x,v)) for (n,x,y),(m,v) in zip(sorted(clean,key=lambda r:r[0]),available)]
    return {'available':available,'assigned':assigned,
            'missing':[(n,x-v) for (n,x,y),(m,v) in zip(sorted(clean,key=lambda r:r[0]),assigned)]}
