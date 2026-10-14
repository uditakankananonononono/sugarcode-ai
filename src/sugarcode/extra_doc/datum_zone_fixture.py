"""Row 1542, GD&T.

datum_zone_fixture computes maximum supplied x,y coordinate counts and
checks an inclusive square count zone at limit. Returns sorted distances,
inside and outside labels, and limit. No GD&T interpretation, geometric
tolerance symbols, physical datum validation, standards compliance,
metrology instructions or engineering certification is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
limit defaults to 4, an exact int from 0 to 10.
Validation order: rows type, rows size, limit, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: GD&T interpretation, standards compliance, physical datum validation, engineering certification, production readiness.
"""

SCOPE = 'PARTIAL: supplied coordinate count square-zone membership, no GD&T interpretation'
NOT_CLAIMED = ('GD&T interpretation', 'standards compliance', 'physical datum validation', 'engineering certification', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def datum_zone_fixture(rows, limit=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(limit) is not int or not 0 <= limit <= 10:
        raise ValueError('limit must be a nonbool integer between 0 and 10')
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
    distances=sorted((n,max(x,y)) for n,x,y in clean)
    return {'distances':distances,'inside':[n for n,v in distances if v<=limit],
            'outside':[n for n,v in distances if v>limit],'limit':limit}
