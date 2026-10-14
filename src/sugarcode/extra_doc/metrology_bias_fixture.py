"""Row 1543, Metrology.

metrology_bias_fixture subtracts supplied reference y and fixed offset
from reading x counts. Returns sorted bias, absolute_total, balanced as
zero signed sum and offset. No instrument calibration, measurement
uncertainty, traceability, physical units or measurement certification
is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
offset defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, offset, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: instrument calibration, measurement uncertainty, traceability, physical units, production readiness.
"""

SCOPE = 'PARTIAL: supplied reading/reference count bias correction, no instrument calibration'
NOT_CLAIMED = ('instrument calibration', 'measurement uncertainty', 'traceability', 'physical units', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def metrology_bias_fixture(rows, offset=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(offset) is not int or not 0 <= offset <= 5:
        raise ValueError('offset must be a nonbool integer between 0 and 5')
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
    values=sorted((n,x-y-offset) for n,x,y in clean)
    return {'bias':values,'absolute_total':sum(abs(v) for n,v in values),
            'balanced':sum(v for n,v in values)==0,'offset':offset}
