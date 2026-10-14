"""Row 1357, Yield Curve Construction.

yieldcurve_linear_fixture linearly interpolates supplied x at term zero
and y at term ten on an abstract count grid, no extrapolation. Returns sorted
yields as Fraction strings, upward labels where y exceeds x, and term.
No market curve, instrument selection, bootstrapping, calibration, bond
pricing, financial suitability or investment advice is implemented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
term defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, term, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: market yield curve, bootstrapping, bond pricing, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: interpolates supplied two-endpoint integer grids, no market curve'
NOT_CLAIMED = ('market yield curve', 'bootstrapping', 'bond pricing', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def yieldcurve_linear_fixture(rows, term=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(term) is not int or not 0 <= term <= 10:
        raise ValueError('term must be a nonbool integer between 0 and 10')
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
    from fractions import Fraction as F
    values=[(n,F(x*(10-term)+y*term,10)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'yields':[(n,str(v)) for n,v in values],'upward':[n for n,x,y in sorted(clean,key=lambda r:r[0]) if y>x],
            'term':term}
