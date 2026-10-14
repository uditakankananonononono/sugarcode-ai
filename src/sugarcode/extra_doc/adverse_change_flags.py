"""Row 1129, Adverse Event Detection.

adverse_change_flags treats x,y as supplied before/after event counts, not
medical events identified by the function. Returns changes as sorted
(label,y-x), flagged as sorted (label,change-tolerance) only when change
strictly exceeds tolerance, decreased as sorted negative-change labels.
It does not establish event identity, adverse significance or causal relation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
tolerance defaults to 5, an exact int from 0 to 100.
Validation order: rows type, rows size, tolerance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: adverse event identity, causality, clinical significance, event provenance, production readiness.
"""

SCOPE = 'PARTIAL: flags supplied event-count increases above a supplied tolerance, no adverse event is detected'
NOT_CLAIMED = ('adverse event identity', 'causality', 'clinical significance', 'event provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def adverse_change_flags(rows, tolerance=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(tolerance) is not int or not 0 <= tolerance <= 100:
        raise ValueError('tolerance must be a nonbool integer between 0 and 100')
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
    changes = [(n, after - before) for n, before, after in sorted(clean, key=lambda r: r[0])]
    flagged = [(n, change - tolerance) for n, change in changes if change > tolerance]
    decreased = [n for n, change in changes if change < 0]
    return {'changes': changes, 'flagged': flagged, 'decreased': decreased}
