"""Row 1119, Drug Interaction Checking.

interaction_windows treats x,y as endpoints of caller-supplied half-open
administration windows in either order. Compute pairwise positive overlap
length; retain lengths at least minimum. Returns overlaps as sorted-label
(label_a,label_b,length) in pair order, involved as sorted participating
labels. Adjacent windows do not overlap. This time-overlap inventory says
nothing about drug interactions, pharmacology or clinical safety.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
minimum defaults to 1, an exact int from 1 to 5.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: drug interaction, clinical safety, pharmacology, administration advice, production readiness.
"""

SCOPE = 'PARTIAL: reports overlaps of supplied administration windows, no drug interactions are inferred'
NOT_CLAIMED = ('drug interaction', 'clinical safety', 'pharmacology', 'administration advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def interaction_windows(rows, minimum=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 1 <= minimum <= 5:
        raise ValueError('minimum must be a nonbool integer between 1 and 5')
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
    nodes = sorted([(n, min(x, y), max(x, y)) for n, x, y in clean])
    overlaps = []
    for i, (a, lo, hi) in enumerate(nodes):
        for b, left, right in nodes[i+1:]:
            duration = max(0, min(hi, right) - max(lo, left))
            if duration >= minimum:
                overlaps.append((a, b, duration))
    involved = sorted({n for a, b, d in overlaps for n in (a, b)})
    return {'overlaps': overlaps, 'involved': involved}
