"""Row 1559, Humidity Testing.

humidity_dose_fixture multiplies the nonnegative excess of supplied
level x count over baseline by supplied duration y count. Returns sorted
doses, total, zero labels and baseline. No humidity testing, moisture
prediction, physical dose estimate, environmental response model, physical
units or engineering safety judgement is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
baseline defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, baseline, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: humidity testing, moisture prediction, physical dose estimate, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied excess-level/duration count exposure dose, no humidity testing'
NOT_CLAIMED = ('humidity testing', 'moisture prediction', 'physical dose estimate', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def humidity_dose_fixture(rows, baseline=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(baseline) is not int or not 0 <= baseline <= 10:
        raise ValueError('baseline must be a nonbool integer between 0 and 10')
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
    values=sorted((n,max(0,x-baseline)*y) for n,x,y in clean)
    return {'doses':values,'total':sum(v for n,v in values),'zero':[n for n,v in values if v==0],
            'baseline':baseline}
