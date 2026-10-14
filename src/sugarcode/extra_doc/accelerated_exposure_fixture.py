"""Row 1554, Accelerated Life Testing.

accelerated_exposure_fixture multiplies supplied duration x count by
stress y plus one raised to power. Returns sorted exposures, total,
maximum and power. This is a fixed count multiplier, not accelerated life
model, lifetime prediction, physical stress validation, physical units,
experimental test execution or engineering safety.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
power defaults to 2, an exact int from 1 to 4.
Validation order: rows type, rows size, power, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: accelerated life model, lifetime prediction, physical stress validation, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied duration/stress count exposure multiplier, no accelerated life model'
NOT_CLAIMED = ('accelerated life model', 'lifetime prediction', 'physical stress validation', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def accelerated_exposure_fixture(rows, power=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(power) is not int or not 1 <= power <= 4:
        raise ValueError('power must be a nonbool integer between 1 and 4')
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
    values=sorted((n,x*(y+1)**power) for n,x,y in clean)
    return {'exposures':values,'total':sum(v for n,v in values),'maximum':max(v for n,v in values),
            'power':power}
