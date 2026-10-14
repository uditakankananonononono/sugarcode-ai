"""Row 1342, Sortino Ratio.

sortino_squared_fixture forms abstract excess counts x minus y minus target. Population
downside deviation uses mean of squared negative excess, with zero contribution
from nonnegative excess. Returns squared ratio Fraction string or None at zero
downside, sign, defined and below-target labels. No annualization, real return
series, target suitability, market risk or investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
target defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, target, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: real Sortino estimate, annualization, market data, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: reports exact squared downside count ratio, no real Sortino estimate'
NOT_CLAIMED = ('real Sortino estimate', 'annualization', 'market data', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def sortino_squared_fixture(rows, target=2):
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
    values=[x-y-target for n,x,y in clean]
    total=sum(values); downside=sum(min(0,v)**2 for v in values)
    squared=F(total*total,len(values)*downside) if downside else None
    return {'squared':str(squared) if squared is not None else None,'sign':(total>0)-(total<0),
            'defined':downside!=0,'below':sorted(n for n,x,y in clean if x-y<target)}
