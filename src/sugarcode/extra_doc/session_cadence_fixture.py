"""Row 1152, Psychotherapy Planning.

session_cadence_fixture expands each supplied start x and positive step y
through an inclusive integer horizon. Returns slots (integer_time,label)
sorted by time then label, collisions as distinct times with multiple labels,
empty as sorted labels whose start exceeds horizon. No calendar or treatment
plan is created; times are abstract fixture indices.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
horizon defaults to 6, an exact int from 0 to 20.
Validation order: rows type, rows size, horizon, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: psychotherapy planning, clinical session needs, treatment, calendar booking, production readiness.
"""

SCOPE = 'PARTIAL: expands supplied integer cadence fixtures, no psychotherapy planning'
NOT_CLAIMED = ('psychotherapy planning', 'clinical session needs', 'treatment', 'calendar booking', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def session_cadence_fixture(rows, horizon=6):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(horizon) is not int or not 0 <= horizon <= 20:
        raise ValueError('horizon must be a nonbool integer between 0 and 20')
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
    slots = []
    for n, start, step in sorted(clean, key=lambda r:r[0]):
        slots.extend((t,n) for t in range(start,horizon+1,step))
    slots.sort(key=lambda r:(r[0],r[1]))
    collisions = sorted(t for t in {t for t,n in slots} if sum(a==t for a,n in slots)>1)
    return {'slots': slots, 'collisions': collisions, 'empty': sorted(n for n,start,step in clean if start>horizon)}
