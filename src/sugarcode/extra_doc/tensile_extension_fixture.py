"""Row 1566, Tensile Testing.

tensile_extension_fixture divides scale times supplied load x count by
supplied stiffness y count plus one. Returns sorted extensions Fraction
strings, total Fraction string, at_least_one inclusive labels and scale.
No tensile testing, physical deformation prediction, material strength
estimate, constitutive law, physical units or engineering safety.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
scale defaults to 3, an exact int from 1 to 5.
Validation order: rows type, rows size, scale, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: tensile testing, physical deformation prediction, material strength estimate, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied load/stiffness count extension ratio, no tensile testing'
NOT_CLAIMED = ('tensile testing', 'physical deformation prediction', 'material strength estimate', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def tensile_extension_fixture(rows, scale=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(scale) is not int or not 1 <= scale <= 5:
        raise ValueError('scale must be a nonbool integer between 1 and 5')
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
    values=sorted((n,F(scale*x,y+1)) for n,x,y in clean)
    return {'extensions':[(n,str(v)) for n,v in values],'total':str(sum(v for n,v in values)),
            'at_least_one':[n for n,v in values if v>=1],'scale':scale}
