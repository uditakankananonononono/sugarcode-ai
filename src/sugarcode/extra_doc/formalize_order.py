"""Row 877, Ontology Development - Formalizes concepts.

formalize_order declares a precedes b when both b's attributes exceed a's
by at least margin. This is a strict partial order. Returns covers as sorted
(a,b) pairs without any intermediate concept c satisfying a<c<b, minimal
as sorted labels with no predecessor, maximal as sorted labels with no
successor. Disconnected and coincident concepts are retained as labels.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
margin defaults to 1, an exact int from 1 to 5.
Validation order: rows type, rows size, margin, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: ontology inference, logical reasoning, semantic truth, OWL interoperability, production readiness.
"""

SCOPE = 'PARTIAL: derives cover relations from supplied two-attribute dominance, no real ontology is inferred'
NOT_CLAIMED = ('ontology inference', 'logical reasoning', 'semantic truth', 'OWL interoperability', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def formalize_order(rows, margin=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(margin) is not int or not 1 <= margin <= 5:
        raise ValueError('margin must be a nonbool integer between 1 and 5')
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
    nodes = sorted(clean, key=lambda r: r[0])
    relation = {(a, b) for a, x, y in nodes for b, u, v in nodes
                if u - x >= margin and v - y >= margin}
    covers = sorted((a, b) for a, b in relation
                    if not any((a, c) in relation and (c, b) in relation for c, _, _ in nodes))
    minimal = [n for n, _, _ in nodes if not any(b == n for a, b in relation)]
    maximal = [n for n, _, _ in nodes if not any(a == n for a, b in relation)]
    return {'covers': covers, 'minimal': minimal, 'maximal': maximal}
