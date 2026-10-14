"""Row 1153, CBT Protocol Design.

step_quota_fixture splits remaining max(0,x-y) abstract units into full
chunk units followed by one smaller remainder when needed. Returns plans
as sorted (label,list_of_chunk_sizes), step_count as total chunks, done as
labels needing zero chunks. No CBT activities or clinical protocols are used.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
chunk defaults to 3, an exact int from 1 to 10.
Validation order: rows type, rows size, chunk, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: CBT protocol, psychotherapy, treatment efficacy, clinical safety, production readiness.
"""

SCOPE = 'PARTIAL: chunks abstract supplied work counts, no CBT protocol design'
NOT_CLAIMED = ('CBT protocol', 'psychotherapy', 'treatment efficacy', 'clinical safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def step_quota_fixture(rows, chunk=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(chunk) is not int or not 1 <= chunk <= 10:
        raise ValueError('chunk must be a nonbool integer between 1 and 10')
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
    plans = []
    for n, x, y in sorted(clean, key=lambda r:r[0]):
        left = max(0, x - y)
        steps = []
        while left:
            take = min(chunk, left)
            steps.append(take)
            left -= take
        plans.append((n, steps))
    return {'plans': plans, 'step_count': sum(len(s) for n,s in plans),
            'done': [n for n,s in plans if not s]}
