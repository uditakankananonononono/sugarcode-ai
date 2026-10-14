"""Row 1333, Markowitz Model.

markowitz_diagonal_fixture treats x as supplied diagonal variance-count and
y as mean-return-count under fixed equal weights and zero cross-covariance.
Returns mean, variance and mean minus scale times variance utility as Fraction strings,
and count. No weights are optimized, covariance/returns estimated or actual
Markowitz portfolio, market risk or investment advice supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
scale defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, scale, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: Markowitz optimization, covariance inference, market returns, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: evaluates equal-weight diagonal variance count fixtures, no Markowitz optimization'
NOT_CLAIMED = ('Markowitz optimization', 'covariance inference', 'market returns', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def markowitz_diagonal_fixture(rows, scale=2):
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
    count=len(clean)
    mean=F(sum(y for n,x,y in clean),count)
    variance=F(sum(x for n,x,y in clean),count*count)
    utility=mean-scale*variance
    return {'mean':str(mean),'variance':str(variance),'utility':str(utility),'count':count}
