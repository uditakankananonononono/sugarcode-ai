"""Row 1399, Green Bonds.

green_use_fixture compares supplied allocated count x to proceeds count
y. Returns sorted uses (label,capped_allocated,unallocated,overallocated),
within_tolerance labels where total discrepancy meets tolerance,
unallocated and overallocated totals. Eligibility is unverified. No actual
green-bond assessment, taxonomy compliance, valuation or advice is given.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tolerance defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, tolerance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: green bond assessment, taxonomy compliance, bond valuation, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied allocated/proceeds count bookkeeping, no green-bond assessment'
NOT_CLAIMED = ('green bond assessment', 'taxonomy compliance', 'bond valuation', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def green_use_fixture(rows, tolerance=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(tolerance) is not int or not 0 <= tolerance <= 5:
        raise ValueError('tolerance must be a nonbool integer between 0 and 5')
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
    values=sorted((n,min(x,y),max(y-x,0),max(x-y,0)) for n,x,y in clean)
    return {'uses':values,'within_tolerance':[n for n,a,u,o in values if u+o<=tolerance],
            'unallocated':sum(u for n,a,u,o in values),'overallocated':sum(o for n,a,u,o in values)}
