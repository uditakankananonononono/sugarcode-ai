"""Row 1258, Zoning and Land Use.

zoning_grid_fixture removes border abstract unit cells from each side of
supplied x by y rectangles and floors interior lengths at zero. Returns
sorted interiors, empty zero labels and total cells. No actual land, zoning,
setback rule, geography, development rights or permit is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
border defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, border, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: zoning or land use, legal setbacks, geographic validation, permit eligibility, production readiness.
"""

SCOPE = 'PARTIAL: clips supplied abstract rectangle grid units, no zoning or land use analysis'
NOT_CLAIMED = ('zoning or land use', 'legal setbacks', 'geographic validation', 'permit eligibility', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def zoning_grid_fixture(rows, border=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(border) is not int or not 0 <= border <= 5:
        raise ValueError('border must be a nonbool integer between 0 and 5')
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
    interiors=[(n,max(0,x-2*border)*max(0,y-2*border)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'interiors':interiors,'empty':[n for n,v in interiors if v==0],
            'total':sum(v for n,v in interiors)}
