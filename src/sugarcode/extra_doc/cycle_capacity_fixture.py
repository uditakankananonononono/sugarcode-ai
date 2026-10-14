"""Row 1159, Asthma Management.

cycle_capacity_fixture computes ceil((x+reserve)/y) for supplied positive
abstract load x and capacity y. Returns label-sorted cycles (label,count,
spare_capacity_in_last_cycle), total_cycles and full labels with zero spare.
No inhaler use, lung function, safety or asthma care is interpreted.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
reserve defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, reserve, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: asthma management, inhaler regimen, clinical risk, treatment, production readiness.
"""

SCOPE = 'PARTIAL: calculates abstract capacity cycles, no asthma management'
NOT_CLAIMED = ('asthma management', 'inhaler regimen', 'clinical risk', 'treatment', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def cycle_capacity_fixture(rows, reserve=1):
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
        if type(x) is not int or not 1 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 1 and 10')
        if type(y) is not int or not 1 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 1 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    cycles = []
    for n, load, capacity in sorted(clean,key=lambda r:r[0]):
        total = load + reserve
        count = (total + capacity - 1) // capacity
        spare = count * capacity - total
        cycles.append((n,count,spare))
    return {'cycles':cycles,'total_cycles':sum(c for n,c,s in cycles),
            'full':[n for n,c,s in cycles if s==0]}
