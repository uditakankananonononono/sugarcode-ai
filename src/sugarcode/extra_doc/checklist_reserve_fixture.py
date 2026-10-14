"""Row 1202, Suicide Prevention.

checklist_reserve_fixture treats x as abstract requested checklist units and
y as abstract supplied units. Returns coverage (label,matched minimum of x and y,nonnegative
shortfall of x plus reserve minus y), no_gap zero-shortfall labels, total_gap and total_matched.
All labels and counts are opaque fixtures. No symptoms, suicidal thoughts,
intent or protective factors are interpreted. No suicide risk is predicted,
prevention effectiveness claimed, safety certified or intervention advised.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
reserve defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, reserve, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: suicide prevention, suicide risk prediction, clinical safety, intervention recommendations, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied checklist reserve counts, no suicide prevention or risk assessment'
NOT_CLAIMED = ('suicide prevention', 'suicide risk prediction', 'clinical safety', 'intervention recommendations', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def checklist_reserve_fixture(rows, reserve=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(reserve) is not int or not 0 <= reserve <= 10:
        raise ValueError('reserve must be a nonbool integer between 0 and 10')
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
    coverage=[(n,min(x,y),max(0,x+reserve-y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'coverage':coverage,'no_gap':[n for n,c,g in coverage if g==0],
            'total_gap':sum(g for n,c,g in coverage),'total_matched':sum(c for n,c,g in coverage)}
