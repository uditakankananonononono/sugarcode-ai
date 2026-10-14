"""Row 1535, Ergonomics.

ergonomic_offset_fixture computes Manhattan offsets of supplied x,y
coordinate counts from (target,target). Returns sorted offsets, nearest
tied labels, total and target. This is abstract coordinate bookkeeping,
not ergonomics assessment, human reach prediction, physical unit mapping,
posture advice, comfort judgement or engineering safety validation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
target defaults to 4, an exact int from 0 to 10.
Validation order: rows type, rows size, target, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: ergonomics assessment, human reach prediction, physical units, safety judgement, production readiness.
"""

SCOPE = 'PARTIAL: supplied coordinate count reach offset, no ergonomics assessment'
NOT_CLAIMED = ('ergonomics assessment', 'human reach prediction', 'physical units', 'safety judgement', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ergonomic_offset_fixture(rows, target=4):
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
    offsets=sorted((n,abs(x-target)+abs(y-target)) for n,x,y in clean)
    best=min(v for n,v in offsets)
    return {'offsets':offsets,'nearest':[n for n,v in offsets if v==best],
            'total':sum(v for n,v in offsets),'target':target}
