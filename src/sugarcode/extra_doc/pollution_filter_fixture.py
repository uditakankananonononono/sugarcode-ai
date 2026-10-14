"""Row 1261, Pollution Control.

pollution_filter_fixture retains keep y tenths of abstract count x per pass,
flooring each step. Returns sorted residual (label,remaining,removed), zero
labels and total_removed. No filter, emissions, pollution impact or actual
control efficacy or safety is validated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
passes defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, passes, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: pollution control, filter efficacy, actual emissions, environmental safety, production readiness.
"""

SCOPE = 'PARTIAL: iterates abstract count retention, no pollution control'
NOT_CLAIMED = ('pollution control', 'filter efficacy', 'actual emissions', 'environmental safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def pollution_filter_fixture(rows, passes=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(passes) is not int or not 0 <= passes <= 5:
        raise ValueError('passes must be a nonbool integer between 0 and 5')
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
    residual=[]
    for n,count,keep in sorted(clean,key=lambda r:r[0]):
        value=count
        for _ in range(passes): value=value*keep//10
        residual.append((n,value,count-value))
    return {'residual':residual,'zero':[n for n,v,removed in residual if v==0],
            'total_removed':sum(r for n,v,r in residual)}
