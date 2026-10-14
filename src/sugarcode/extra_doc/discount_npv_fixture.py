"""Row 1323, NPV Calculation.

discount_npv_fixture treats x as nonnegative cash-count fixture and y as
integer period. Discount x by (1+rate/100) to power y, including period zero.
Returns sorted discounted Fraction strings, present_sum and undiscounted
sum. No initial outlay is inferred, so this is a present-value sum, not a full
signed investment NPV. No source validity, real valuation or advice is claimed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
rate defaults to 10, an exact int from 0 to 100.
Validation order: rows type, rows size, rate, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: real valuation, cash provenance, initial investment inference, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: discounts supplied nonnegative cash-count fixtures, no investment advice'
NOT_CLAIMED = ('real valuation', 'cash provenance', 'initial investment inference', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def discount_npv_fixture(rows, rate=10):
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
    discounted=[(n,F(x)*F(100,100+rate)**y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'discounted':[(n,str(v)) for n,v in discounted],
            'present_sum':str(sum((v for n,v in discounted),F(0))),
            'undiscounted':sum(x for n,x,y in clean)}
