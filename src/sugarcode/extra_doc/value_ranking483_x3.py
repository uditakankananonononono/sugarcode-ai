"""Row483 Values Definition - Articulates principles.
Supplied-data helper only. Rows (label, rank 1..32), unique ranks. Return labels ordered by rank and whether ranks are exactly 1..n.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: adopted values, principles being right or external effects.
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


def analyze_value_ranking(rows):
    _rows(rows, 'values', 32, 2)
    for row in rows:
        _label(row[0])
        _integer(row[1], 1, 32)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('value labels must be unique')
    if len({row[1] for row in rows}) != len(rows):
        raise ValueError('value ranks must be unique')
    ordered=sorted(rows,key=lambda r:r[1])
    ranks=[row[1] for row in ordered]
    return {'order':[row[0] for row in ordered],'contiguous':ranks==list(range(1,len(rows)+1)),'values_adopted':False}
