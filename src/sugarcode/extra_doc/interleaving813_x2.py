"""Row813 Interleaving - Mixes practice types.
Supplied category task queues only. Rows(label,task_count0..32),1..32 unique
labels. Return deterministic rounds: each lexically sorted category with
remaining tasks emits(label,one_based_task_index) once per round.
NOT_CLAIMED: effective practice, optimal mixing, task validity, learning
outcomes, actual practice execution or external effects.
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


def round_robin_practice(rows):
    _rows(rows,'categories',32,2)
    for label,count in rows:_label(label);_integer(count,0,32)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('category labels must be unique')
    sequence=[]
    for index in range(1,max(count for _,count in rows)+1):
        for label,count in sorted(rows):
            if index<=count:sequence.append((label,index))
    return {'sequence':sequence,'practice_optimized':False}
