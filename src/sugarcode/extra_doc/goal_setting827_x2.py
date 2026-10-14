"""Row827 Goal Setting - Defines objectives.
Supplied objective target/current/deadline ledger only. Rows(label,target1..100,
current0..100,deadline0..1000000),1..32;as_of0..1000000. Report met goals and
unmet goals grouped as overdue iff deadline<as_of,otherwise pending.
NOT_CLAIMED: useful goals, motivation, meaningful objectives, verified
progress, goal enforcement or external effects.
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


def declared_goal_status(rows,as_of):
    _rows(rows,'goals',32,4);_integer(as_of,0,1000000)
    for label,target,current,deadline in rows:_label(label);_integer(target,1,100);_integer(current,0,100);_integer(deadline,0,1000000)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('goal labels must be unique')
    met=[];overdue=[];pending=[]
    for label,target,current,deadline in sorted(rows):
        if current>=target:met.append(label)
        elif deadline<as_of:overdue.append((label,target-current))
        else:pending.append((label,target-current))
    return {'met':met,'overdue':overdue,'pending':pending,'progress_verified':False}
