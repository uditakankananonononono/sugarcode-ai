"""Row 1142, Occupational Therapy Design.

task_fit_fixture treats x as supplied abstract demand and y as supplied
capacity. Deficit=max(0,x-y-slack). Returns fits as sorted zero-deficit labels,
gaps as sorted (label,deficit), worst as largest deficit. Equality fits.
These are abstract scalar fixtures, not occupational-therapy design or real
functional ability, and no therapeutic recommendation is made.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
slack defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, slack, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: occupational therapy, functional ability, clinical regimen, patient suitability, production readiness.
"""

SCOPE = 'PARTIAL: compares supplied task demand against supplied capacity with fixed slack'
NOT_CLAIMED = ('occupational therapy', 'functional ability', 'clinical regimen', 'patient suitability', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def task_fit_fixture(rows, slack=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(slack) is not int or not 0 <= slack <= 5:
        raise ValueError('slack must be a nonbool integer between 0 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 100:
            raise ValueError('x must be a nonbool integer between 0 and 100')
        if type(y) is not int or not 0 <= y <= 100:
            raise ValueError('y must be a nonbool integer between 0 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    fits = []
    gaps = []
    for n, demand, capacity in sorted(clean, key=lambda r: r[0]):
        gap = max(0, demand - capacity - slack)
        gaps.append((n, gap))
        if gap == 0:
            fits.append(n)
    return {'fits': fits, 'gaps': gaps, 'worst': max(g for n, g in gaps)}
