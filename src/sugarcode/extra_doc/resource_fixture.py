"""Row 1135, ICU Resource Allocation.

resource_fixture treats x as integer item cost and y as supplied item value.
Select a subset under capacity maximizing value, then minimizing cost, then
lexicographic sorted label tuple. Empty subset is allowed. Returns selected
sorted labels, value as total supplied value, used as total cost, remaining
as capacity-used. These are abstract fixtures, not ICU allocation or patient
benefit assessments, and no real resources are committed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
capacity defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, capacity, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: clinical allocation, patient benefit, capacity validity, real resource commitment, production readiness.
"""

SCOPE = 'PARTIAL: solves a bounded supplied integer resource menu, no ICU resources are allocated'
NOT_CLAIMED = ('clinical allocation', 'patient benefit', 'capacity validity', 'real resource commitment', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def resource_fixture(rows, capacity=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(capacity) is not int or not 0 <= capacity <= 10:
        raise ValueError('capacity must be a nonbool integer between 0 and 10')
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
    from itertools import product
    nodes = sorted(clean, key=lambda r: r[0])
    best = (0, 0, ())
    for bits in product((0, 1), repeat=len(nodes)):
        cost = sum(r[1] * bit for r, bit in zip(nodes, bits))
        value = sum(r[2] * bit for r, bit in zip(nodes, bits))
        names = tuple(r[0] for r, bit in zip(nodes, bits) if bit)
        if cost <= capacity and (-value, cost, names) < (-best[0], best[1], best[2]):
            best = (value, cost, names)
    return {'selected': list(best[2]), 'value': best[0], 'used': best[1], 'remaining': capacity - best[1]}
