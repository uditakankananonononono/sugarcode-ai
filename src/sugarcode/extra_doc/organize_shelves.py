"""Row 875, Knowledge Organization - Structures information.

organize_shelves treats x+y as each label's storage size. Process descending
size, label ascending on ties. Reject sizes greater than capacity; otherwise
put each label on the first shelf with room or open a shelf. Zero sizes fit.
Returns shelves as label lists in creation/placement order, loads as each
shelf's total size, rejected as oversized labels in processing order.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
capacity defaults to 100, an exact int from 1 to 200.
Validation order: rows type, rows size, capacity, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: knowledge understanding, optimal packing, semantic organization, size estimation, production readiness.
"""

SCOPE = 'PARTIAL: first-fit-decreasing packing of supplied information sizes, no knowledge is understood'
NOT_CLAIMED = ('knowledge understanding', 'optimal packing', 'semantic organization', 'size estimation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def organize_shelves(rows, capacity=100):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(capacity) is not int or not 1 <= capacity <= 200:
        raise ValueError('capacity must be a nonbool integer between 1 and 200')
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
    shelves = []
    loads = []
    rejected = []
    for label, x, y in sorted(clean, key=lambda r: (-(r[1] + r[2]), r[0])):
        size = x + y
        if size > capacity:
            rejected.append(label)
            continue
        for i, load in enumerate(loads):
            if load + size <= capacity:
                shelves[i].append(label)
                loads[i] += size
                break
        else:
            shelves.append([label])
            loads.append(size)
    return {'shelves': shelves, 'loads': loads, 'rejected': rejected}
