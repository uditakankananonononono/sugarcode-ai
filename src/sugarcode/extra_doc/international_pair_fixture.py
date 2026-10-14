"""Row 1278, International Law.

international_pair_fixture sorts each abstract pair into low/high counts.
Returns pairs sorted by label, both counts at least floor, one count at least
floor, neither otherwise. No state conduct, jurisdiction, international legal
rights, treaties or obligations are evaluated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
floor defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, floor, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: international law, jurisdiction, treaty applicability, legal rights, production readiness.
"""

SCOPE = 'PARTIAL: pools abstract supplied reciprocal tallies, no international law analysis'
NOT_CLAIMED = ('international law', 'jurisdiction', 'treaty applicability', 'legal rights', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def international_pair_fixture(rows, floor=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(floor) is not int or not 0 <= floor <= 10:
        raise ValueError('floor must be a nonbool integer between 0 and 10')
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
    pairs=[(n,min(x,y),max(x,y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'pairs':pairs,'both':[n for n,a,b in pairs if a>=floor],
            'one':[n for n,a,b in pairs if a<floor<=b],
            'neither':[n for n,a,b in pairs if b<floor]}
