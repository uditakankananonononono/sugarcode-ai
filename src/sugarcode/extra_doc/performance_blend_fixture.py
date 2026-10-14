"""Row 1471, Performance Prediction.

performance_blend_fixture blends supplied prior x and practice y counts
with percent weight on prior and remaining weight on practice. Returns
sorted blends Fraction strings, total and above_prior labels where blend
strictly exceeds x. No actual performance prediction, fitted statistical
model, learner diagnosis or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 60, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: performance prediction, statistical model, learner diagnosis, production readiness.
"""

SCOPE = 'PARTIAL: supplied prior/practice count linear blend, no performance prediction'
NOT_CLAIMED = ('performance prediction', 'statistical model', 'learner diagnosis', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def performance_blend_fixture(rows, percent=60):
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
    return {'blends':[(n,str(v)) for n,v in values],'total':str(sum((v for n,v in values),F(0))),
            'above_prior':sorted(n for n,x,y in clean if percent<100 and y>x)}
