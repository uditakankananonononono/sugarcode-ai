"""Row851 Non-Monotonic Reasoning - Revises conclusions.
Supplied ordered assertion/retraction bit events only. Rows(label,fact0..15,
asserted bool),1..32. Starting from empty active set, true adds fact,false
removes if present. Return sorted final facts and per-event active count.
NOT_CLAIMED: justified belief revision, evidence quality, logical consistency,
real-world truth, autonomous decisions or external effects.
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


def declared_fact_revisions(rows):
    _rows(rows,'events',32,3)
    for label,fact,asserted in rows:
        _label(label);_integer(fact,0,15)
        if type(asserted) is not bool:raise TypeError('revision flags must be exact bool')
    if len({r[0] for r in rows})!=len(rows):raise ValueError('event labels must be unique')
    active=set();counts=[]
    for label,fact,asserted in rows:
        if asserted:active.add(fact)
        else:active.discard(fact)
        counts.append((label,len(active)))
    return {'facts':sorted(active),'active_counts':counts,'beliefs_verified':False}
