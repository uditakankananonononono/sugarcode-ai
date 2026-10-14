"""Row 1524, Thermal Analysis.

thermal_resistance_fixture multiplies supplied temperature count x minus
ambient by positive conductance count y plus one. Returns sorted fluxes,
outward positive and inward negative labels, net signed sum. No physical
units, thermal simulation, material validation, transient behavior,
boundary condition model or engineering safety claim is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
ambient defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, ambient, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: thermal simulation, physical units, material validation, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied temperature/conductance count flux, no thermal simulation'
NOT_CLAIMED = ('thermal simulation', 'physical units', 'material validation', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def thermal_resistance_fixture(rows, ambient=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(ambient) is not int or not 0 <= ambient <= 10:
        raise ValueError('ambient must be a nonbool integer between 0 and 10')
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
    values=sorted((n,(x-ambient)*(y+1)) for n,x,y in clean)
    return {'fluxes':values,'outward':[n for n,v in values if v>0],
            'inward':[n for n,v in values if v<0],'net':sum(v for n,v in values)}
