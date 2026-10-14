"""Row 1244, Immigration Law.

immigration_points_fixture combines abstract supplied tallies as twice x
plus y. Returns sorted points, met labels at least cutoff and nonnegative
gaps. No government policy, immigration eligibility, jurisdictional rule or
legal status is verified or inferred.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
cutoff defaults to 10, an exact int from 0 to 30.
Validation order: rows type, rows size, cutoff, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: immigration law, eligibility, legal advice, government policy verification, production readiness.
"""

SCOPE = 'PARTIAL: combines supplied abstract point tallies, no immigration law advice'
NOT_CLAIMED = ('immigration law', 'eligibility', 'legal advice', 'government policy verification', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def immigration_points_fixture(rows, cutoff=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(cutoff) is not int or not 0 <= cutoff <= 30:
        raise ValueError('cutoff must be a nonbool integer between 0 and 30')
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
    points=[(n,2*x+y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'points':points,'met':[n for n,v in points if v>=cutoff],
            'gaps':[(n,max(0,cutoff-v)) for n,v in points]}
