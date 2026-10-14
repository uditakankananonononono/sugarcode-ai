"""Row820 Problem Solving - Practices application.
Supplied bounded two-operation arithmetic puzzle only. Rows(label,start0..100,
target0..100),1..32;max_steps0..8. Each step adds1 or doubles;values above100
not visited. Return minimum steps if reachable within cap,otherwiseNone.
NOT_CLAIMED: general problem solving, useful real-world plans, application
skills, optimal human actions, execution or external effects.
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


def bounded_arithmetic_paths(rows,max_steps):
    _rows(rows,'puzzles',32,3);_integer(max_steps,0,8)
    for label,start,target in rows:_label(label);_integer(start,0,100);_integer(target,0,100)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('puzzle labels must be unique')
    results=[]
    for label,start,target in sorted(rows):
        frontier={start};seen={start};distance=None
        for depth in range(max_steps+1):
            if target in frontier:distance=depth;break
            following={value for current in frontier for value in (current+1,current*2) if value<=100}-seen
            seen|=following;frontier=following
        results.append((label,distance))
    return {'steps':results,'problem_solving_evaluated':False}
