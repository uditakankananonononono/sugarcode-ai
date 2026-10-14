"""Row 1338, Asset Allocation.

allocation_weight_fixture computes abstract positive score multiplier times x plus y
then normalizes by total. Returns sorted weight Fraction strings, scores and
total score. No actual assets, capital, risk tolerance, investment suitability,
portfolio recommendation or commitment is assessed or executed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
multiplier defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, multiplier, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: asset allocation advice, risk suitability, actual assets, capital commitment, production readiness.
"""

SCOPE = 'PARTIAL: normalizes supplied positive asset count tokens, no asset allocation advice'
NOT_CLAIMED = ('asset allocation advice', 'risk suitability', 'actual assets', 'capital commitment', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def allocation_weight_fixture(rows, multiplier=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(multiplier) is not int or not 1 <= multiplier <= 5:
        raise ValueError('multiplier must be a nonbool integer between 1 and 5')
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
    scores=[(n,multiplier*x+y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    total=sum(v for n,v in scores)
    return {'weights':[(n,str(F(v,total))) for n,v in scores],'scores':scores,'total':total}
