"""Row 1210, Patient Safety.

safety_limit_fixture computes supplied limit y minus event count x minus
margin. Returns sorted margins, breached labels with negative remaining
margin, all_within and minimum remaining margin. No real hazard or patient
safety judgment is possible from these abstract caller-supplied fixtures.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
margin defaults to 1, an exact int from 0 to 10.
Validation order: rows type, rows size, margin, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: patient safety, hazard detection, clinical safety, causal risk, production readiness.
"""

SCOPE = 'PARTIAL: tests abstract supplied event counts against numeric limits, no patient safety guarantee'
NOT_CLAIMED = ('patient safety', 'hazard detection', 'clinical safety', 'causal risk', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def safety_limit_fixture(rows, margin=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(margin) is not int or not 0 <= margin <= 10:
        raise ValueError('margin must be a nonbool integer between 0 and 10')
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
    margins=[(n,y-x-margin) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'margins':margins,'breached':[n for n,v in margins if v<0],
            'all_within':all(v>=0 for n,v in margins),'minimum':min(v for n,v in margins)}
