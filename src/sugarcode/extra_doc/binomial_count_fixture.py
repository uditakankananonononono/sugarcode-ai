"""Row 1349, Binomial Trees.

binomial_count_fixture averages abstract supplied two-branch payoff counts
x/y with fixed probability one half, then discounts one period by rate percent.
Returns sorted values as Fraction strings, total and equal_branches labels.
No underlying price dynamics, calibrated/risk-neutral probability, multi-step
or American exercise tree, market price or investment advice is implemented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
rate defaults to 10, an exact int from 0 to 100.
Validation order: rows type, rows size, rate, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: calibrated binomial pricing, risk-neutral probability, multi-step tree, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: evaluates one-step equal-probability supplied payoff counts, no calibrated binomial pricing'
NOT_CLAIMED = ('calibrated binomial pricing', 'risk-neutral probability', 'multi-step tree', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def binomial_count_fixture(rows, rate=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(rate) is not int or not 0 <= rate <= 100:
        raise ValueError('rate must be a nonbool integer between 0 and 100')
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
    values=[(n,F((x+y)*100,2*(100+rate))) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'values':[(n,str(v)) for n,v in values],'total':str(sum((v for n,v in values),F(0))),
            'equal_branches':sorted(n for n,x,y in clean if x==y)}
