"""Row 1252, Estate Planning.

estate_residual_fixture subtracts abstract reserve y from units x, floors
at zero and divides by parts. Returns sorted shares (label,quotient,remainder),
remainders as sum of remainder units and empty zero quotient/remainder labels.
No real assets, tax rules, beneficiary rights or legal estate plan is used.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
parts defaults to 3, an exact int from 1 to 10.
Validation order: rows type, rows size, parts, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: estate planning, asset valuation, tax advice, legal entitlement, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied remainder shares, no estate planning'
NOT_CLAIMED = ('estate planning', 'asset valuation', 'tax advice', 'legal entitlement', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def estate_residual_fixture(rows, parts=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(parts) is not int or not 1 <= parts <= 10:
        raise ValueError('parts must be a nonbool integer between 1 and 10')
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
    shares=[]
    for n,units,reserve in sorted(clean,key=lambda r:r[0]):
        left=max(0,units-reserve)
        q,r=divmod(left,parts)
        shares.append((n,q,r))
    return {'shares':shares,'remainders':sum(r for n,q,r in shares),
            'empty':[n for n,q,r in shares if q==0 and r==0]}
