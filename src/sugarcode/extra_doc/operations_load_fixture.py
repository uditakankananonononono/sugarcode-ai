"""Row 1212, Healthcare Operations.

operations_load_fixture sums supplied abstract work counts x and y and
ceil-divides each by capacity. Returns sorted loads and batches, total_batches
and idle labels of zero load. No staffing adequacy, hospital operations or
clinical throughput is inferred or executed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
capacity defaults to 5, an exact int from 1 to 10.
Validation order: rows type, rows size, capacity, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: healthcare operations, staffing adequacy, clinical safety, external execution, production readiness.
"""

SCOPE = 'PARTIAL: computes abstract work load ceilings, no healthcare operations execution'
NOT_CLAIMED = ('healthcare operations', 'staffing adequacy', 'clinical safety', 'external execution', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def operations_load_fixture(rows, capacity=5):
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
    loads=[(n,x+y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    batches=[(n,(v+capacity-1)//capacity) for n,v in loads]
    return {'loads':loads,'batches':batches,'total_batches':sum(b for n,b in batches),
            'idle':[n for n,v in loads if v==0]}
