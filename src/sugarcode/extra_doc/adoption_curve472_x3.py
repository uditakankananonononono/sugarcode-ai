"""Row472 Change Management - Guides transitions.
Supplied-data helper only. Rows (label, week 0..52, new adopters 0..1000), unique weeks. Return the cumulative adopter curve by week and the first week reaching at least half the total (None if the total is 0).
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a successful change, people being guided or external effects.
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


def analyze_adoption_curve(rows):
    _rows(rows, 'weeks', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 52)
        _integer(row[2], 0, 1000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('week labels must be unique')
    if len({row[1] for row in rows}) != len(rows):
        raise ValueError('week numbers must be unique')
    ordered=sorted(rows,key=lambda r:r[1])
    total=sum(row[2] for row in rows)
    running=0
    curve=[]
    half=None
    for row in ordered:
        running+=row[2]
        curve.append((row[1],running))
        if half is None and total>0 and 2*running>=total:
            half=row[1]
    return {'adoption':curve,'half_week':half,'change_succeeded':False}
