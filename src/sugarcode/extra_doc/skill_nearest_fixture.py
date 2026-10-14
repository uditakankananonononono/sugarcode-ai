"""Row 1154, DBT Skill Selection.

skill_nearest_fixture computes Manhattan distance of supplied (x,y) to
(target,target). Returns scored (label,distance) sorted by distance then
label, nearest as all minimum-distance labels, exact as zero-distance
labels. The labels are opaque fixtures, not DBT skills or recommendations.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
target defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, target, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: DBT skill selection, clinical suitability, therapy, safety, production readiness.
"""

SCOPE = 'PARTIAL: ranks abstract paired points by target distance, no DBT skill selection'
NOT_CLAIMED = ('DBT skill selection', 'clinical suitability', 'therapy', 'safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def skill_nearest_fixture(rows, target=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(target) is not int or not 0 <= target <= 10:
        raise ValueError('target must be a nonbool integer between 0 and 10')
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
    scored = [(n, abs(x-target)+abs(y-target)) for n,x,y in clean]
    scored.sort(key=lambda r:(r[1],r[0]))
    best = scored[0][1]
    return {'scored':scored,'nearest':[n for n,d in scored if d==best],
            'exact':[n for n,d in scored if d==0]}
