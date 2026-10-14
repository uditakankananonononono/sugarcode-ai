"""Row466 DMAIC - Define-Measure-Analyze-Improve-Control.
Supplied-data helper only. Rows (label, stage 0..4 = define/measure/analyze/improve/control, minutes 0..1000) in input order. Return minutes per stage and labels whose stage is lower than an earlier stage seen.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: process improvement, statistical control, a real project or external effects.
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


def analyze_dmaic_flow(rows):
    _rows(rows, 'steps', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 4)
        _integer(row[2], 0, 1000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('step labels must be unique')
    minutes=[0,0,0,0,0]
    high=-1
    late=[]
    for label,stage,spent in rows:
        minutes[stage]+=spent
        if stage<high:
            late.append(label)
        high=max(high,stage)
    return {'stage_minutes':minutes,'out_of_order':late,'improvement_verified':False}
