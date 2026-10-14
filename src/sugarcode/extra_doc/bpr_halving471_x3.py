"""Row471 Business Process Reengineering - Redesigns fundamentally.
Supplied-data helper only. Rows (label, old steps 0..100, new steps 0..100). Return step change per label and the labels whose new count is at most half the old count (old above 0).
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a real redesign, savings, business value or external effects.
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


def analyze_bpr_halving(rows):
    _rows(rows, 'processes', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 100)
        _integer(row[2], 0, 100)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('process labels must be unique')
    ordered=sorted(rows,key=lambda r:r[0])
    return {'changes':[(row[0],row[1]-row[2]) for row in ordered],'radical':[row[0] for row in ordered if row[1]>0 and 2*row[2]<=row[1]],'redesign_verified':False}
