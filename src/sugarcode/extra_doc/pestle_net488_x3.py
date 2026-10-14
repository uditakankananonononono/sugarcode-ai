"""Row488 PESTLE Analysis - Scans environment.
Supplied-data helper only. Rows (label, factor 0..5 = political/economic/social/technological/legal/environmental, impact -5..5). Return the net per factor and the smallest factor index with the largest absolute net (None when all are 0).
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a scanned environment, external facts or effects.
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


def analyze_pestle_net(rows):
    _rows(rows, 'factors', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 5)
        _integer(row[2], -5, 5)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('factor labels must be unique')
    nets=[0,0,0,0,0,0]
    for row in rows:
        nets[row[1]]+=row[2]
    big=max(abs(value) for value in nets)
    return {'nets':nets,'dominant':None if big==0 else min(index for index,value in enumerate(nets) if abs(value)==big),'environment_scanned':False}
