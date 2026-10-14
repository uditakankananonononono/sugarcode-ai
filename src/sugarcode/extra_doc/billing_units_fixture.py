"""Row 1312, Legal Billing.

billing_units_fixture multiplies abstract time x and rate y tokens then
reduces their product by discount percent. Returns sorted amount Fraction
strings, total string and zero labels. No actual time, money, legal fee,
invoice, entitlement or payment is verified, created or executed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
discount defaults to 20, an exact int from 0 to 100.
Validation order: rows type, rows size, discount, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal billing, real money, fee entitlement, invoice or payment, production readiness.
"""

SCOPE = 'PARTIAL: multiplies supplied abstract billing count tokens, no legal billing'
NOT_CLAIMED = ('legal billing', 'real money', 'fee entitlement', 'invoice or payment', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def billing_units_fixture(rows, discount=20):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(discount) is not int or not 0 <= discount <= 100:
        raise ValueError('discount must be a nonbool integer between 0 and 100')
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
    amounts=[(n,F(x*y*(100-discount),100)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'amounts':[(n,str(v)) for n,v in amounts],'total':str(sum((v for n,v in amounts),F(0))),
            'zero':[n for n,v in amounts if v==0]}
