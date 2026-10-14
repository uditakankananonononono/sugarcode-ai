"""Row 1452, Online Learning.

online_completion_fixture caps supplied completed count y at assigned
module count x and computes completion share, undefined at zero assignments.
Returns sorted completion Fraction strings or None, meeting inclusive
percent, excess labels where y exceeds x, and empty. No online course
delivery, learning effectiveness, completion verification or recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 75, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: online course delivery, learning effectiveness, completion verification, production readiness.
"""

SCOPE = 'PARTIAL: supplied module/completion count ratio, no online course delivery'
NOT_CLAIMED = ('online course delivery', 'learning effectiveness', 'completion verification', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def online_completion_fixture(rows, percent=75):
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
    values=sorted((n,F(min(x,y),x) if x else None) for n,x,y in clean)
    return {'completion':[(n,str(v)) if v is not None else (n,None) for n,v in values],
            'meeting':[n for n,v in values if v is not None and v>=F(percent,100)],
            'excess':sorted(n for n,x,y in clean if y>x),'empty':[n for n,v in values if v is None]}
