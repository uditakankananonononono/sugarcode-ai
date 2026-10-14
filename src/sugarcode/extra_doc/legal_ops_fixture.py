"""Row 1310, Legal Operations.

legal_ops_fixture sums abstract paired workload counts and ceil-divides by
capacity. Returns sorted workloads, batches, total_batches and zero-load labels.
No staffing adequacy, real throughput, legal accuracy or operations action
is verified, inferred or executed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
capacity defaults to 5, an exact int from 1 to 10.
Validation order: rows type, rows size, capacity, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal operations, staffing adequacy, legal accuracy, external execution, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied task throughput, no legal operations execution'
NOT_CLAIMED = ('legal operations', 'staffing adequacy', 'legal accuracy', 'external execution', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def legal_ops_fixture(rows, capacity=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(capacity) is not int or not 1 <= capacity <= 10:
        raise ValueError('capacity must be a nonbool integer between 1 and 10')
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
    workloads=[(n,x+y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    batches=[(n,(v+capacity-1)//capacity) for n,v in workloads]
    return {'workloads':workloads,'batches':batches,'total_batches':sum(v for n,v in batches),
            'zero':[n for n,v in workloads if v==0]}
