"""Row824 Fading - Removes support gradually.
Supplied support decrement arithmetic only. Rows(label,support0..100,
decrement0..100),1..32. Return nonnegative new support and actual removed
amount. This rule does not decide whether reducing support is appropriate.
NOT_CLAIMED: effective support fading, learner readiness, accessibility,
training outcomes, actual support changes or external effects.
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


def declared_support_decrements(rows):
    _rows(rows,'supports',32,3)
    for label,support,decrement in rows:_label(label);_integer(support,0,100);_integer(decrement,0,100)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('support labels must be unique')
    return {'supports':[(label,max(support-decrement,0),min(support,decrement)) for label,support,decrement in sorted(rows,key=lambda r:r[0])],'readiness_evaluated':False}
