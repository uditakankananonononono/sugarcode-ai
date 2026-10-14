"""Row819 Worked Examples - Shows solutions.
Supplied running-total worked trace only. Rows(label,delta-1000..1000,
claimed_total-32000..32000),1..32 ordered steps;initial-1000..1000.
Compare each claim to initial plus all preceding/current deltas. Return
ordered mismatches and final computed total; labels unique.
NOT_CLAIMED: actual solutions, pedagogical quality, explanation validity,
learning effectiveness, general problem solving or external effects.
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


def running_total_trace(rows,initial):
    _rows(rows,'steps',32,3);_integer(initial,-1000,1000)
    for label,delta,claim in rows:_label(label);_integer(delta,-1000,1000);_integer(claim,-32000,32000)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('step labels must be unique')
    total=initial;mismatches=[]
    for label,delta,claim in rows:
        total+=delta
        if claim!=total:mismatches.append((label,total))
    return {'mismatches':mismatches,'final_total':total,'learning_evaluated':False}
