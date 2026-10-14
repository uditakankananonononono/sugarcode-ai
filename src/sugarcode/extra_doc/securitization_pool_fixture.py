"""Row 1365, Securitization.

securitization_pool_fixture pools positive supplied collateral x minus
obligation y counts and splits equally among units, giving remainder units
to earlier zero-based indices. Returns sorted contributions, pool, integer
allocation and remainder. No securitization transaction, legal structure,
tranche analysis, real instrument valuation or advice is implemented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
units defaults to 3, an exact int from 1 to 5.
Validation order: rows type, rows size, units, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: securitization transaction, legal structure, tranche valuation, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: pools supplied positive collateral surplus counts, no securitization'
NOT_CLAIMED = ('securitization transaction', 'legal structure', 'tranche valuation', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def securitization_pool_fixture(rows, units=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(units) is not int or not 1 <= units <= 5:
        raise ValueError('units must be a nonbool integer between 1 and 5')
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
    contributions=sorted((n,max(x-y,0)) for n,x,y in clean)
    pool=sum(v for n,v in contributions); quotient,remainder=divmod(pool,units)
    return {'contributions':contributions,'pool':pool,
            'allocation':[quotient+(i<remainder) for i in range(units)],'remainder':remainder}
