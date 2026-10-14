"""Row 1334, Black-Litterman.

blacklitterman_blend_fixture blends abstract supplied prior x and view y
counts with prior_weight to one. Returns sorted blend Fraction strings,
raised labels whose view exceeds prior and lowered labels otherwise less.
This scalar averaging has no equilibrium, covariance, view matrix, confidence
or Bayesian portfolio model; no real Black-Litterman result/advice is claimed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
prior_weight defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, prior_weight, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: Black-Litterman model, covariance or confidence inference, market equilibrium, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: blends abstract prior/view counts with scalar weight, no Black-Litterman model'
NOT_CLAIMED = ('Black-Litterman model', 'covariance or confidence inference', 'market equilibrium', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def blacklitterman_blend_fixture(rows, prior_weight=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(prior_weight) is not int or not 1 <= prior_weight <= 5:
        raise ValueError('prior_weight must be a nonbool integer between 1 and 5')
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
    blends=[(n,F(prior_weight*x+y,prior_weight+1)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'blends':[(n,str(v)) for n,v in blends],
            'raised':sorted(n for n,x,y in clean if y>x),'lowered':sorted(n for n,x,y in clean if y<x)}
