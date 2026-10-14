"""Row 1213, Hospital Administration.

department_queue_fixture computes x plus bias times y on abstract supplied counts.
Returns scores descending then label, queue labels in that order and ties
as all equal-score label pairs in queue order. No clinical priority, staffing
adequacy, hospital decisions or external operations are performed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
bias defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, bias, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: hospital administration, staffing adequacy, clinical priority, external execution, production readiness.
"""

SCOPE = 'PARTIAL: orders abstract supplied department counts, no hospital administration'
NOT_CLAIMED = ('hospital administration', 'staffing adequacy', 'clinical priority', 'external execution', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def department_queue_fixture(rows, bias=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(bias) is not int or not 0 <= bias <= 5:
        raise ValueError('bias must be a nonbool integer between 0 and 5')
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
    scored=[(n,x+bias*y) for n,x,y in clean]
    scored.sort(key=lambda r:(-r[1],r[0]))
    return {'queue':[n for n,v in scored],'scores':scored,
            'ties':[(a,b) for i,(a,u) in enumerate(scored) for b,v in scored[i+1:] if u==v]}
