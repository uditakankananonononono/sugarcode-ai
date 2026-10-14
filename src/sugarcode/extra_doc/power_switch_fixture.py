"""Row 1585, Power Electronics.

power_switch_fixture divides supplied on x count by on plus off y
count plus one and multiplies on-plus-off count by cycles. Returns sorted
duties Fraction strings, ticks count pairs, total_ticks and cycles. No
power electronics validation, switching circuit safety, physical efficiency
estimate, actual duty-cycle waveform or component selection is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
cycles defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, cycles, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: power electronics validation, switching circuit safety, physical efficiency estimate, component selection, production readiness.
"""

SCOPE = 'PARTIAL: supplied on/off count duty fraction, no power electronics validation'
NOT_CLAIMED = ('power electronics validation', 'switching circuit safety', 'physical efficiency estimate', 'component selection', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def power_switch_fixture(rows, cycles=2):
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
    from fractions import Fraction as F
    values=sorted((n,F(x,x+y+1),cycles*(x+y)) for n,x,y in clean)
    return {'duties':[(n,str(v)) for n,v,t in values],'ticks':[(n,t) for n,v,t in values],
            'total_ticks':sum(t for n,v,t in values),'cycles':cycles}
