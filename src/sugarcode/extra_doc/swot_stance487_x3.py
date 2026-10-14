"""Row487 SWOT Analysis - Assesses position.
Supplied-data helper only. Rows (label, quadrant 0..3 = strength/weakness/opportunity/threat, score 0..10). Net internal = S-W, external = O-T; a net must be above 0 to count as positive. Stance: grow, defend, pivot or retrench.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a real position, market facts or external effects.
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


def analyze_swot_stance(rows):
    _rows(rows, 'items', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 3)
        _integer(row[2], 0, 10)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('item labels must be unique')
    totals=[0,0,0,0]
    for row in rows:
        totals[row[1]]+=row[2]
    inner=totals[0]-totals[1]
    outer=totals[2]-totals[3]
    if inner>0:
        stance='grow' if outer>0 else 'defend'
    else:
        stance='pivot' if outer>0 else 'retrench'
    return {'quadrants':totals,'internal':inner,'external':outer,'stance':stance,'position_assessed':False}
