"""Row818 Concrete Examples - Illustrates abstract.
Supplied interval-rule numeric example checker only. Rows(label,lower integer
-1000..1000,upper same,example same),1..32;lower<=upper. Classify example
within inclusive interval or outside and report nearest endpoint correction.
NOT_CLAIMED: illustrative quality, conceptual understanding, abstraction,
semantic example validity, teaching effectiveness or external effects.
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


def interval_example_checks(rows):
    _rows(rows,'examples',32,4)
    for label,lower,upper,value in rows:
        _label(label);_integer(lower,-1000,1000);_integer(upper,-1000,1000);_integer(value,-1000,1000)
        if lower>upper:raise ValueError('lower must not exceed upper')
    if len({r[0] for r in rows})!=len(rows):raise ValueError('example labels must be unique')
    inside=[];corrections=[]
    for label,lower,upper,value in sorted(rows):
        if lower<=value<=upper:inside.append(label)
        else:corrections.append((label,lower if value<lower else upper))
    return {'inside':inside,'corrections':corrections,'understanding_evaluated':False}
