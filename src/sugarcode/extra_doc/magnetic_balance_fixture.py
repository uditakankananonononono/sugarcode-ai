"""Row 1574, Magnetic Particle Testing.

magnetic_balance_fixture multiplies supplied indication x minus
background y count by gain. Returns sorted signals, positive strict labels,
absolute_total and gain. No magnetic particle testing, defect detection,
physical field simulation, material inspection, physical units or
engineering safety judgement is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
gain defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, gain, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: magnetic particle testing, defect detection, physical field simulation, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied indication/background count amplified difference, no magnetic particle testing'
NOT_CLAIMED = ('magnetic particle testing', 'defect detection', 'physical field simulation', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def magnetic_balance_fixture(rows, gain=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(gain) is not int or not 1 <= gain <= 5:
        raise ValueError('gain must be a nonbool integer between 1 and 5')
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
    values=sorted((n,gain*(x-y)) for n,x,y in clean)
    return {'signals':values,'positive':[n for n,v in values if v>0],
            'absolute_total':sum(abs(v) for n,v in values),'gain':gain}
