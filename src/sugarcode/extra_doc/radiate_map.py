"""Row 874, Mind Mapping - Radiates associations.

radiate_map assigns each (label, x, y) association to spoke x modulo spokes,
with radius y. Returns branches as a list of spokes lists, each containing
(label, radius) ordered by radius ascending then label; occupied as the
number of nonempty spokes; outermost as the maximum-radius label with
lexicographically smallest label breaking ties. Empty spokes remain present.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
spokes defaults to 4, an exact int from 1 to 5.
Validation order: rows type, rows size, spokes, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: association generation, visual rendering, semantic proximity, mind reading, production readiness.
"""

SCOPE = 'PARTIAL: places supplied associations on numbered radial spokes, no associations are generated'
NOT_CLAIMED = ('association generation', 'visual rendering', 'semantic proximity', 'mind reading', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def radiate_map(rows, spokes=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(spokes) is not int or not 1 <= spokes <= 5:
        raise ValueError('spokes must be a nonbool integer between 1 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 100:
            raise ValueError('x must be a nonbool integer between 0 and 100')
        if type(y) is not int or not 0 <= y <= 100:
            raise ValueError('y must be a nonbool integer between 0 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    branches = [[] for _ in range(spokes)]
    for label, branch, radius in clean:
        branches[branch % spokes].append((label, radius))
    for branch in branches:
        branch.sort(key=lambda p: (p[1], p[0]))
    return {'branches': branches, 'occupied': sum(bool(b) for b in branches),
            'outermost': min(clean, key=lambda r: (-r[2], r[0]))[0]}
