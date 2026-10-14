"""Row 869, Reframing - Changes perspective: one cost stated per different unit.

reframe_cost takes total, a nonbool int from 1 to 1000000 (a cost in cents),
and units, a list or tuple of 1 to 5 (unit, count) tuples. unit is a printable
ASCII string of 1 to 12 characters (control characters are refused), distinct
across units. count is a nonbool int from 1 to 10000, how many of that unit
the total is spread over.
Each unit gives a new view of the same total: the cost per unit in whole
cents, rounded down, and the cents left over.
Returns frames (a list of (unit, per_unit, left_over) with the biggest count
first and ties by unit name, so the smallest per_unit comes first), gentlest
(the unit of the first frame), steepest (the unit of the last frame) and
spread (steepest per_unit minus gentlest per_unit). Per unit times count plus
left over always equals total.
Checks, in this order: total, units type, units size, each entry (shape, unit,
count), distinct units.
NOT_CLAIMED: real reframing, persuasion effect, fair unit choice, learner
perspective taking, production readiness.
"""

SCOPE = 'PARTIAL: restates a supplied total per supplied unit count, no perspective is changed'
NOT_CLAIMED = ('real reframing', 'persuasion effect', 'fair unit choice',
               'learner perspective taking', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def reframe_cost(total, units):
    if type(total) is not int or not 1 <= total <= 1000000:
        raise ValueError('total must be a nonbool integer between 1 and 1000000')
    if type(units) not in (list, tuple):
        raise TypeError('units must be a list or tuple')
    if not 1 <= len(units) <= 5:
        raise ValueError('units must contain 1 to 5 entries')
    rows = []
    for u in units:
        if type(u) not in (list, tuple) or len(u) != 2:
            raise ValueError('each entry must be a (unit, count) tuple')
        unit, count = u
        if not _label(unit):
            raise ValueError('each unit must be a printable ASCII string of 1 to 12 characters')
        if type(count) is not int or not 1 <= count <= 10000:
            raise ValueError('count must be a nonbool integer between 1 and 10000')
        rows.append((unit, count))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('units must be distinct')
    rows.sort(key=lambda r: (-r[1], r[0]))
    frames = [(unit, total // count, total % count) for unit, count in rows]
    return {'frames': frames, 'gentlest': frames[0][0], 'steepest': frames[-1][0],
            'spread': frames[-1][1] - frames[0][1]}
