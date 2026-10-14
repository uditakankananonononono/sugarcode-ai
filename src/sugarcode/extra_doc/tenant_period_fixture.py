"""Row 1257, Landlord-Tenant.

tenant_period_fixture compares abstract periods times required x to supplied
y, flooring arrears at zero. Returns sorted arrears, zero labels, total and
excess labels above requirement. No money, rent, eviction rights, legal notice
or landlord/tenant obligations are interpreted.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
periods defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, periods, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: landlord-tenant law, rent valuation, eviction or notice advice, legal obligations, production readiness.
"""

SCOPE = 'PARTIAL: inventories supplied abstract period arrears, no landlord-tenant legal advice'
NOT_CLAIMED = ('landlord-tenant law', 'rent valuation', 'eviction or notice advice', 'legal obligations', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def tenant_period_fixture(rows, periods=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(periods) is not int or not 0 <= periods <= 10:
        raise ValueError('periods must be a nonbool integer between 0 and 10')
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
    arrears=[(n,max(0,periods*x-y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'arrears':arrears,'zero':[n for n,v in arrears if v==0],
            'total':sum(v for n,v in arrears),'excess':sorted(n for n,x,y in clean if y>periods*x)}
