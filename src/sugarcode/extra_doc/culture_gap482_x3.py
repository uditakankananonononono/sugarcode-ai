"""Row482 Culture Design - Shapes values and norms.
Supplied-data helper only. Rows (label, desired 0..10, actual 0..10). Return desired minus actual per label and the labels sharing the largest positive gap.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: changed culture, real values or external effects.
"""
def _rows(value, name, cap, arity):
    if type(value) not in (list, tuple): raise TypeError(name + ': exact list or tuple required')
    if not 1 <= len(value) <= cap: raise ValueError(name + ': row count outside declared range')
    for row in value:
        if type(row) not in (list, tuple): raise TypeError(name + ': exact list or tuple row required')
        if len(row) != arity: raise ValueError(name + ': wrong row arity')


def _label(value):
    if type(value) is not str: raise TypeError('exact string label required')
    if not 1 <= len(value) <= 24 or not value.isascii() or not all(c.isalnum() or c == '_' for c in value):
        raise ValueError('label must be 1..24 ASCII word characters')


def _integer(value, lo, hi):
    if type(value) is not int: raise TypeError('exact nonbool integer required')
    if not lo <= value <= hi: raise ValueError('integer outside declared range')


def analyze_culture_gap(rows):
    _rows(rows, 'norms', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 10)
        _integer(row[2], 0, 10)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('norm labels must be unique')
    gaps=[(row[0],row[1]-row[2]) for row in sorted(rows,key=lambda r:r[0])]
    top=max(gap for _,gap in gaps)
    return {'gaps':gaps,'largest':[label for label,gap in gaps if gap==top and gap>0],'culture_changed':False}
