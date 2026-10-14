"""Row 1555, Environmental Testing.

environment_buffer_fixture takes the minimum supplied paired tolerance
x,y count and subtracts reserve. Returns sorted buffers, nonnegative
inclusive labels, minimum and reserve. No environmental testing, physical
tolerance validation, test certification, environmental chamber operation,
physical units or engineering safety judgement is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
reserve defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, reserve, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: environmental testing, physical tolerance validation, test certification, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied paired tolerance count minimum buffer, no environmental testing'
NOT_CLAIMED = ('environmental testing', 'physical tolerance validation', 'test certification', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def environment_buffer_fixture(rows, reserve=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(reserve) is not int or not 0 <= reserve <= 5:
        raise ValueError('reserve must be a nonbool integer between 0 and 5')
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
    values=sorted((n,min(x,y)-reserve) for n,x,y in clean)
    return {'buffers':values,'nonnegative':[n for n,v in values if v>=0],
            'minimum':min(v for n,v in values),'reserve':reserve}
