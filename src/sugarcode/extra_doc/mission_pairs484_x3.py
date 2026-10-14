"""Row484 Mission Statement Creation - Defines purpose.
Supplied-data helper only. Rows (label, audience 0..7, outcome 0..7, weight 1..10). Return summed weight per audience/outcome pair and the smallest pair holding the maximum.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a real mission, purpose or external effects.
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


def analyze_mission_pairs(rows):
    _rows(rows, 'statements', 32, 4)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 7)
        _integer(row[2], 0, 7)
        _integer(row[3], 1, 10)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('statement labels must be unique')
    totals={}
    for row in rows:
        totals[(row[1],row[2])]=totals.get((row[1],row[2]),0)+row[3]
    pairs=sorted(totals.items(),key=lambda item:item[0])
    best=max(value for _,value in pairs)
    return {'pairs':pairs,'primary':min(key for key,value in pairs if value==best),'mission_valid':False}
