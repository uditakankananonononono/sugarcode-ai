"""Row 1529, Material Properties.

material_mix_fixture linearly blends supplied property counts x and y
with percent weight on x. Returns sorted blends Fraction strings, minimum
and maximum Fraction strings, equal_inputs labels. No actual mixture law,
material property prediction, physical units, experimental validation,
material compatibility or engineering safety claim is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 40, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: material property prediction, physical units, experimental validation, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied two-property count linear blend, no material property prediction'
NOT_CLAIMED = ('material property prediction', 'physical units', 'experimental validation', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def material_mix_fixture(rows, percent=40):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(percent) is not int or not 0 <= percent <= 100:
        raise ValueError('percent must be a nonbool integer between 0 and 100')
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
    values=sorted((n,F(percent*x+(100-percent)*y,100)) for n,x,y in clean)
    return {'blends':[(n,str(v)) for n,v in values],'minimum':str(min(v for n,v in values)),
            'maximum':str(max(v for n,v in values)),'equal_inputs':sorted(n for n,x,y in clean if x==y)}
