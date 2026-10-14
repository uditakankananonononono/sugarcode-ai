"""Row 876, Taxonomy Creation - Classifies.

classify_taxonomy assigns major=x//cell and minor=y//cell for every label.
Returns paths as (label, major, minor) sorted by label, tree as major keys
mapping to minor keys mapping to sorted label lists (integer keys ascending),
leaves as the number of occupied (major, minor) classes, not number of labels.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
cell defaults to 10, an exact int from 1 to 100.
Validation order: rows type, rows size, cell, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: taxonomy inference, biological classification, semantic classes, class usefulness, production readiness.
"""

SCOPE = 'PARTIAL: assigns supplied coordinates to two-level grid classes, no taxonomy is inferred'
NOT_CLAIMED = ('taxonomy inference', 'biological classification', 'semantic classes', 'class usefulness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def classify_taxonomy(rows, cell=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(cell) is not int or not 1 <= cell <= 100:
        raise ValueError('cell must be a nonbool integer between 1 and 100')
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
    paths = [(n, x // cell, y // cell) for n, x, y in sorted(clean, key=lambda r: r[0])]
    tree = {}
    for n, major, minor in paths:
        tree.setdefault(major, {}).setdefault(minor, []).append(n)
    tree = {a: {b: tree[a][b] for b in sorted(tree[a])} for a in sorted(tree)}
    return {'paths': paths, 'tree': tree,
            'leaves': sum(len(children) for children in tree.values())}
