"""Row 1305, Legal Technology.

legaltech_queue_fixture expands abstract nonnegative pending x minus y task tokens into
(label,index) items and batches in label/index order. Returns batches, total
and empty labels. No software is deployed, legal work executed, source
accuracy verified or system suitability certified.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
batch defaults to 3, an exact int from 1 to 10.
Validation order: rows type, rows size, batch, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal technology deployment, system suitability, legal accuracy, external execution, production readiness.
"""

SCOPE = 'PARTIAL: batches abstract supplied task count tokens, no legal technology deployment'
NOT_CLAIMED = ('legal technology deployment', 'system suitability', 'legal accuracy', 'external execution', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def legaltech_queue_fixture(rows, batch=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(batch) is not int or not 1 <= batch <= 10:
        raise ValueError('batch must be a nonbool integer between 1 and 10')
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
    tasks=[(n,i) for n,x,y in sorted(clean,key=lambda r:r[0]) for i in range(max(0,x-y))]
    batches=[tasks[i:i+batch] for i in range(0,len(tasks),batch)]
    return {'batches':batches,'total':len(tasks),'empty':sorted(n for n,x,y in clean if x<=y)}
