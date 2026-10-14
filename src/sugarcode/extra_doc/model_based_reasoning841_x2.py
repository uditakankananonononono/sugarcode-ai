"""Row841 Model-Based Reasoning - Uses models.
Supplied finite deterministic transition model only. Rows(label,state0..31,
next_state0..31),1..32 unique state keys;start0..31,steps0..32. Return visited
trace, stopping early when a state has no transition. Cycles are permitted.
NOT_CLAIMED: valid real-world model, predictions, general reasoning,
model fitting, actual state transitions or external effects.
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


def declared_transition_trace(rows,start,steps):
    _rows(rows,'transitions',32,3);_integer(start,0,31);_integer(steps,0,32)
    for label,state,next_state in rows:_label(label);_integer(state,0,31);_integer(next_state,0,31)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('transition labels must be unique')
    if len({r[1] for r in rows})!=len(rows):raise ValueError('transition states must be unique')
    model={state:next_state for _,state,next_state in rows};trace=[start]
    for _ in range(steps):
        if trace[-1] not in model:break
        trace.append(model[trace[-1]])
    return {'trace':trace,'model_verified':False}
