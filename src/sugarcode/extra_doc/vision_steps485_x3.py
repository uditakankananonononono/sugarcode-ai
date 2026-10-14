"""Row485 Vision Statement Creation - Paints future.
Supplied-data helper only. Rows (label, year 1..32, target 0..1000), unique years. Return milestones by year, target steps, and whether every step is strictly positive.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a real vision, future outcomes or external effects.
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


def analyze_vision_steps(rows):
    _rows(rows, 'milestones', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 1, 32)
        _integer(row[2], 0, 1000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('milestone labels must be unique')
    if len({row[1] for row in rows}) != len(rows):
        raise ValueError('milestone years must be unique')
    ordered=sorted(rows,key=lambda r:r[1])
    steps=[(later[1],later[2]-earlier[2]) for earlier,later in zip(ordered,ordered[1:])]
    return {'milestones':[(row[1],row[2]) for row in ordered],'steps':steps,'increasing':all(step>0 for _,step in steps),'vision_valid':False}
