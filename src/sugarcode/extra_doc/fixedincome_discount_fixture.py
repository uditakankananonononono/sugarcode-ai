"""Row 1356, Fixed Income Analysis.

fixedincome_discount_fixture treats supplied x as one abstract cash count
due in y periods and rate as tenths per period, discounting by one plus rate
in tenths to that period. Returns sorted present Fraction strings, total and
undiscounted count. No actual bond, coupon schedule, dates, accrued interest,
market data, instrument valuation or investment advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
rate defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, rate, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: instrument valuation, cash flow schedule, market data, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: discounts abstract single cash counts by supplied periods, no instrument analysis'
NOT_CLAIMED = ('instrument valuation', 'cash flow schedule', 'market data', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def fixedincome_discount_fixture(rows, rate=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(rate) is not int or not 0 <= rate <= 5:
        raise ValueError('rate must be a nonbool integer between 0 and 5')
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
    values=[(n,F(x*10**y,(10+rate)**y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'present':[(n,str(v)) for n,v in values],'total':str(sum((v for n,v in values),F(0))),
            'undiscounted':sum(x for n,x,y in clean)}
