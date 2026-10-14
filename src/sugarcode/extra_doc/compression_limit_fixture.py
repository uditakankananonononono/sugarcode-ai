"""Row 1567, Compression Testing.

compression_limit_fixture subtracts steps times supplied compression y
count from supplied height x count, clamping to zero. Returns sorted
heights, collapsed zero labels, removed total difference and steps. No
compression testing, physical deformation prediction, material strength
estimate, physical units or engineering safety judgement is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
steps defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, steps, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: compression testing, physical deformation prediction, material strength estimate, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied height/compression count clamped residual, no compression testing'
NOT_CLAIMED = ('compression testing', 'physical deformation prediction', 'material strength estimate', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def compression_limit_fixture(rows, steps=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(steps) is not int or not 1 <= steps <= 5:
        raise ValueError('steps must be a nonbool integer between 1 and 5')
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
    values=sorted((n,max(0,x-steps*y)) for n,x,y in clean)
    return {'heights':values,'collapsed':[n for n,v in values if v==0],
            'removed':sum(x for n,x,y in clean)-sum(v for n,v in values),'steps':steps}
