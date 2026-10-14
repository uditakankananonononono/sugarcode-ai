"""Row 1255, Real Estate Law.

property_area_fixture multiplies supplied abstract rectangle sides x and y.
Returns label-sorted areas, at_least labels meeting minimum, total and
zero-area degenerate labels. No actual land, boundaries, title, valuation or
real estate legal conclusion is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 20, an exact int from 0 to 100.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: real estate law, title verification, legal property boundaries, valuation, production readiness.
"""

SCOPE = 'PARTIAL: inventories supplied abstract rectangle areas, no real estate law analysis'
NOT_CLAIMED = ('real estate law', 'title verification', 'legal property boundaries', 'valuation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def property_area_fixture(rows, minimum=20):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 0 <= minimum <= 100:
        raise ValueError('minimum must be a nonbool integer between 0 and 100')
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
    areas=[(n,x*y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'areas':areas,'at_least':[n for n,v in areas if v>=minimum],
            'total':sum(v for n,v in areas),'degenerate':[n for n,v in areas if v==0]}
