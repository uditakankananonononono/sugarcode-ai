"""Row 1272, Due Process.

process_step_fixture takes the minimum of abstract supplied notice/hearing
count tokens x and y. Returns sorted counts, met labels at least minimum,
nonnegative gaps and asymmetric unequal-count labels. Tokens have no legal
meaning. No process, fairness, hearing rights or court requirements are assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: due process, procedural fairness, legal rights, court requirements, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied process completion counts, no due process assessment'
NOT_CLAIMED = ('due process', 'procedural fairness', 'legal rights', 'court requirements', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def process_step_fixture(rows, minimum=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 0 <= minimum <= 10:
        raise ValueError('minimum must be a nonbool integer between 0 and 10')
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
    counts=[(n,min(x,y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'counts':counts,'met':[n for n,v in counts if v>=minimum],
            'gaps':[(n,max(0,minimum-v)) for n,v in counts],
            'asymmetric':sorted(n for n,x,y in clean if x!=y)}
