"""Row 878, Semantic Networks - Links meanings.

link_semantics treats x and y as separate four-bit feature masks. Each
unordered pair is linked if its total matching set bits across corresponding
masks is at least shared. Returns links as (label_a, label_b, shared_count)
in lexicographic pair order, adjacency as sorted neighbor lists keyed by
sorted labels, isolated as sorted labels without links. Feature semantics
are supplied by the caller and not interpreted.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 15; bool and all subclasses are refused.
shared defaults to 2, an exact int from 1 to 8.
Validation order: rows type, rows size, shared, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: meaning inference, natural language understanding, semantic truth, feature extraction, production readiness.
"""

SCOPE = 'PARTIAL: links supplied two-feature bit masks by shared-bit count, no meanings are inferred'
NOT_CLAIMED = ('meaning inference', 'natural language understanding', 'semantic truth', 'feature extraction', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def link_semantics(rows, shared=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(shared) is not int or not 1 <= shared <= 8:
        raise ValueError('shared must be a nonbool integer between 1 and 8')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 15:
            raise ValueError('x must be a nonbool integer between 0 and 15')
        if type(y) is not int or not 0 <= y <= 15:
            raise ValueError('y must be a nonbool integer between 0 and 15')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    nodes = sorted(clean, key=lambda r: r[0])
    links = []
    for i, (a, x, y) in enumerate(nodes):
        for b, u, v in nodes[i + 1:]:
            overlap = (x & u).bit_count() + (y & v).bit_count()
            if overlap >= shared:
                links.append((a, b, overlap))
    adjacency = {n: [] for n, _, _ in nodes}
    for a, b, overlap in links:
        adjacency[a].append(b)
        adjacency[b].append(a)
    for neighbors in adjacency.values():
        neighbors.sort()
    return {'links': links, 'adjacency': adjacency,
            'isolated': [n for n in adjacency if not adjacency[n]]}
