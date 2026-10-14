"""Row 1240, Harassment Investigation.

investigation_inventory_fixture sums abstract supplied support x and conflict
y counts. Returns sorted totals, enough labels meeting minimum, conflicted
labels with both counts positive and empty zero labels. No source is retrieved,
credibility assessed, harassment investigated or legal finding made.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 3, an exact int from 0 to 20.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: harassment investigation, credibility determination, legal finding, private source retrieval, production readiness.
"""

SCOPE = 'PARTIAL: inventories supplied abstract evidence tallies, no harassment investigation'
NOT_CLAIMED = ('harassment investigation', 'credibility determination', 'legal finding', 'private source retrieval', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def investigation_inventory_fixture(rows, minimum=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 0 <= minimum <= 20:
        raise ValueError('minimum must be a nonbool integer between 0 and 20')
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
    totals=[(n,x+y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'totals':totals,'enough':[n for n,v in totals if v>=minimum],
            'conflicted':sorted(n for n,x,y in clean if x>0 and y>0),
            'empty':[n for n,v in totals if v==0]}
