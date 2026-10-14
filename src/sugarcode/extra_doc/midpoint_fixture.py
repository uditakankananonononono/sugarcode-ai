"""Row 1158, Hypertension Management.

midpoint_fixture computes exact arithmetic midpoints (x+y)/2 of supplied
abstract pairs. Returns label-sorted midpoint Fraction strings plus above,
equal and below labels compared with target. No blood pressure units, risk
categories or clinical thresholds are interpreted.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
target defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, target, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: hypertension management, blood pressure targets, clinical risk, treatment, production readiness.
"""

SCOPE = 'PARTIAL: compares supplied numeric pair midpoints, no hypertension management'
NOT_CLAIMED = ('hypertension management', 'blood pressure targets', 'clinical risk', 'treatment', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def midpoint_fixture(rows, target=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(target) is not int or not 0 <= target <= 10:
        raise ValueError('target must be a nonbool integer between 0 and 10')
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
    midpoints = [(n,F(x+y,2)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'midpoints':[(n,str(v)) for n,v in midpoints],
            'above':[n for n,v in midpoints if v>target],
            'equal':[n for n,v in midpoints if v==target],
            'below':[n for n,v in midpoints if v<target]}
