"""Row 1237, Employment Law.

employment_hours_fixture sums supplied abstract paired tallies and compares
to caller limit. Returns sorted hours, excess (nonnegative above-limit counts),
over labels strictly above limit and total. No work hours, legal overtime,
wages or employment status is determined.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
limit defaults to 8, an exact int from 0 to 20.
Validation order: rows type, rows size, limit, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: employment law, wage calculation, legal overtime, worker classification, production readiness.
"""

SCOPE = 'PARTIAL: inventories supplied abstract hour tallies, no employment law advice'
NOT_CLAIMED = ('employment law', 'wage calculation', 'legal overtime', 'worker classification', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def employment_hours_fixture(rows, limit=8):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(limit) is not int or not 0 <= limit <= 20:
        raise ValueError('limit must be a nonbool integer between 0 and 20')
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
    hours=[(n,x+y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'hours':hours,'excess':[(n,max(0,v-limit)) for n,v in hours],
            'over':[n for n,v in hours if v>limit],'total':sum(v for n,v in hours)}
