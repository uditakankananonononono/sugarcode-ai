"""Row 1160, COPD Management.

pooled_ratio_fixture computes sum(x)/sum(y) for positive supplied abstract
pairs. Returns ratio as reduced Fraction string, above_percent as inclusive
comparison against percent/100, below_pool as sorted labels whose own x/y
is strictly below the pooled ratio and totals (sum_x,sum_y). No spirometry,
COPD severity or treatment decisions are inferred.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
percent defaults to 50, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: COPD management, spirometry interpretation, clinical prediction, treatment, production readiness.
"""

SCOPE = 'PARTIAL: pools supplied positive numeric ratios, no COPD management'
NOT_CLAIMED = ('COPD management', 'spirometry interpretation', 'clinical prediction', 'treatment', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def pooled_ratio_fixture(rows, percent=50):
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
        if type(x) is not int or not 1 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 1 and 10')
        if type(y) is not int or not 1 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 1 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    numerator = sum(x for n,x,y in clean)
    denominator = sum(y for n,x,y in clean)
    ratio = F(numerator,denominator)
    below = sorted(n for n,x,y in clean if F(x,y) < ratio)
    return {'ratio':str(ratio),'above_percent':100*ratio>=percent,
            'below_pool':below,'totals':(numerator,denominator)}
