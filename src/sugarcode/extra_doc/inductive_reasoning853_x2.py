"""Row853 Inductive Reasoning - Generalizes from specifics.
Supplied category success/attempt count aggregation only. Rows(label,successes
0..100,attempts1..100),1..32;success<=attempts. Return exact pooled rate and
per-label rates. No inference about unseen cases or population.
NOT_CLAIMED: valid generalization, representative samples, statistical
confidence, predictions, population truth or external effects.
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


def declared_pooled_rates(rows):
    _rows(rows,'samples',32,3)
    for label,successes,attempts in rows:
        _label(label);_integer(successes,0,100);_integer(attempts,1,100)
        if successes>attempts:raise ValueError('successes must not exceed attempts')
    if len({r[0] for r in rows})!=len(rows):raise ValueError('sample labels must be unique')
    from fractions import Fraction
    return {'rates':[(label,Fraction(s,a)) for label,s,a in sorted(rows,key=lambda r:r[0])],
            'pooled':Fraction(sum(s for _,s,_ in rows),sum(a for _,_,a in rows)),'generalization_verified':False}
