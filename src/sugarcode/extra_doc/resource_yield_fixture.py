"""Row 1262, Natural Resources.

resource_yield_fixture computes scale times the supplied weighted mean of
abstract yields x with positive weights y. Returns mean Fraction string,
weighted sum, total weight and above labels strictly above the scaled mean.
No resource reserves, value, production or environmental effects are inferred.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
scale defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, scale, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: natural resource assessment, reserves validation, valuation, environmental effects, production readiness.
"""

SCOPE = 'PARTIAL: pools supplied abstract yield weights, no natural resource assessment'
NOT_CLAIMED = ('natural resource assessment', 'reserves validation', 'valuation', 'environmental effects', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def resource_yield_fixture(rows, scale=2):
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
        if type(x) is not int or not 1 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 1 and 10')
        if type(y) is not int or not 1 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 1 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    total_weight=sum(y for n,x,y in clean)
    weighted=sum(x*y for n,x,y in clean)
    mean=F(scale*weighted,total_weight)
    return {'mean':str(mean),'weighted':weighted,'weight':total_weight,
            'above':sorted(n for n,x,y in clean if scale*x>mean)}
