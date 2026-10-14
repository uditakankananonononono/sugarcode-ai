"""Row812 Spaced Repetition - Optimizes review timing.
Supplied deterministic card interval rule only. Rows(label,interval1..10000,
last_day0..1000000,grade0..2),1..32. Grade0 resets interval1,grade1 preserves,
grade2 doubles capped10000. Return sorted(label,new_interval,next_due).
NOT_CLAIMED: optimal timing, learning effectiveness, validated recall grades,
actual review scheduling, personalized learning or external effects.
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


def declared_review_intervals(rows):
    _rows(rows,'cards',32,4)
    for label,interval,day,grade in rows:_label(label);_integer(interval,1,10000);_integer(day,0,1000000);_integer(grade,0,2)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('card labels must be unique')
    result=[]
    for label,interval,day,grade in sorted(rows):
        new=1 if grade==0 else interval if grade==1 else min(10000,interval*2)
        result.append((label,new,day+new))
    return {'reviews':result,'timing_optimized':False}
