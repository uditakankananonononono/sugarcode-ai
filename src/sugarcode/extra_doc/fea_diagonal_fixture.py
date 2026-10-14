"""Row 1522, Finite Element Analysis.

fea_diagonal_fixture solves uncoupled abstract equations stiffness times
displacement equals load_scale times x, with positive stiffness y plus one.
Returns sorted displacements Fraction strings, total and zero labels.
This is a diagonal count-fixture solve, not a finite-element model: no mesh,
assembly, coupling, boundary conditions, physical units or safety claim.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
load_scale defaults to 3, an exact int from 0 to 5.
Validation order: rows type, rows size, load_scale, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: finite element model, meshing, physical units, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: solves supplied uncoupled count spring equations, no finite-element model'
NOT_CLAIMED = ('finite element model', 'meshing', 'physical units', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def fea_diagonal_fixture(rows, load_scale=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(load_scale) is not int or not 0 <= load_scale <= 5:
        raise ValueError('load_scale must be a nonbool integer between 0 and 5')
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
    values=sorted((n,F(load_scale*x,y+1)) for n,x,y in clean)
    return {'displacements':[(n,str(v)) for n,v in values],
            'total':str(sum((v for n,v in values),F(0))),'zero':[n for n,v in values if v==0]}
