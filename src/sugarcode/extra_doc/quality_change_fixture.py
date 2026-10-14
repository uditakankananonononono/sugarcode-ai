"""Row 1209, Healthcare Quality Improvement.

quality_change_fixture subtracts before x from after y in supplied counts.
Returns gains sorted by label, met labels with gain at least required and
total_positive summing only positive gains. Counts have no clinical units;
no causal improvement or healthcare quality standard is established.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
required defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, required, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: healthcare quality certification, clinical outcomes, causal improvement, safety, production readiness.
"""

SCOPE = 'PARTIAL: inventories supplied before/after count improvements, no healthcare quality certification'
NOT_CLAIMED = ('healthcare quality certification', 'clinical outcomes', 'causal improvement', 'safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def quality_change_fixture(rows, required=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(required) is not int or not 0 <= required <= 10:
        raise ValueError('required must be a nonbool integer between 0 and 10')
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
    gains=[(n,y-x) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'gains':gains,'met':[n for n,v in gains if v>=required],
            'total_positive':sum(max(0,v) for n,v in gains)}
