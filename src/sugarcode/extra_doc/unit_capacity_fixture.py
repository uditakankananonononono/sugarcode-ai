"""Row 1424, Unit Planning.

unit_capacity_fixture divides supplied instruction x plus practice y
counts into capacity-sized days independently per unit, rounding days up.
Returns sorted days (label,days,remainder), total_days, partial nonzero
remainder labels and capacity. Zero total uses zero days. No pedagogical
unit plan, activity creation, prerequisite inference or recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
capacity defaults to 4, an exact int from 1 to 10.
Validation order: rows type, rows size, capacity, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: pedagogical unit plan, activity generation, prerequisite inference, production readiness.
"""

SCOPE = 'PARTIAL: packs supplied activity counts into abstract daily capacity, no pedagogical unit plan'
NOT_CLAIMED = ('pedagogical unit plan', 'activity generation', 'prerequisite inference', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def unit_capacity_fixture(rows, capacity=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(capacity) is not int or not 1 <= capacity <= 10:
        raise ValueError('capacity must be a nonbool integer between 1 and 10')
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
    values=sorted((n,(x+y+capacity-1)//capacity,(x+y)%capacity) for n,x,y in clean)
    return {'days':values,'total_days':sum(d for n,d,r in values),
            'partial':[n for n,d,r in values if r>0],'capacity':capacity}
