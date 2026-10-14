"""Row 1286, Discovery.

discovery_batch_fixture expands supplied abstract start/count into opaque
(label,index) items then chunks by batch in label/index order. Returns batches,
count and empty labels. No actual evidence or document is retrieved, privilege
assessed, subpoena issued or legal discovery/court obligation fulfilled.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
batch defaults to 3, an exact int from 1 to 10.
Validation order: rows type, rows size, batch, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal discovery, document retrieval, privilege assessment, court compliance, production readiness.
"""

SCOPE = 'PARTIAL: expands abstract supplied legal-discovery item indices, no legal discovery'
NOT_CLAIMED = ('legal discovery', 'document retrieval', 'privilege assessment', 'court compliance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def discovery_batch_fixture(rows, batch=3):
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
    items=[(n,i) for n,start,count in sorted(clean,key=lambda r:r[0]) for i in range(start,start+count)]
    batches=[items[i:i+batch] for i in range(0,len(items),batch)]
    return {'batches':batches,'count':len(items),'empty':sorted(n for n,start,count in clean if count==0)}
