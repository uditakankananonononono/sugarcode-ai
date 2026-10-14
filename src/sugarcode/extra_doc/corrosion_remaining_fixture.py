"""Row 1560, Corrosion Testing.

corrosion_remaining_fixture subtracts cycles times supplied loss y
count from thickness x count without clamping. Returns sorted remaining,
depleted nonpositive labels, signed total and cycles. No corrosion testing,
physical corrosion prediction, material suitability, structural integrity,
physical units or engineering safety judgement is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
cycles defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, cycles, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: corrosion testing, physical corrosion prediction, material suitability, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied thickness/loss count residual, no corrosion testing'
NOT_CLAIMED = ('corrosion testing', 'physical corrosion prediction', 'material suitability', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def corrosion_remaining_fixture(rows, cycles=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(cycles) is not int or not 1 <= cycles <= 5:
        raise ValueError('cycles must be a nonbool integer between 1 and 5')
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
    values=sorted((n,x-cycles*y) for n,x,y in clean)
    return {'remaining':values,'depleted':[n for n,v in values if v<=0],
            'total':sum(v for n,v in values),'cycles':cycles}
