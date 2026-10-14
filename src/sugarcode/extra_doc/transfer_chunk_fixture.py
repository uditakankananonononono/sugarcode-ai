"""Row 1236, Technology Transfer.

transfer_chunk_fixture chunks remaining max(0,requested x-done y) abstract
units into full batch units then remainder. Returns label-sorted chunks,
batches as total chunk count and complete labels. No technical knowledge,
rights or real transfer readiness is examined or transferred.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
batch defaults to 3, an exact int from 1 to 10.
Validation order: rows type, rows size, batch, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: technology transfer, rights assignment, technical readiness, legal agreement, production readiness.
"""

SCOPE = 'PARTIAL: chunks supplied abstract transfer tallies, no technology transfer'
NOT_CLAIMED = ('technology transfer', 'rights assignment', 'technical readiness', 'legal agreement', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def transfer_chunk_fixture(rows, batch=3):
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
    chunks=[]
    for n,requested,done in sorted(clean,key=lambda r:r[0]):
        need=max(0,requested-done)
        q,r=divmod(need,batch)
        chunks.append((n,[batch]*q+([r] if r else [])))
    return {'chunks':chunks,'batches':sum(len(v) for n,v in chunks),
            'complete':[n for n,v in chunks if not v]}
