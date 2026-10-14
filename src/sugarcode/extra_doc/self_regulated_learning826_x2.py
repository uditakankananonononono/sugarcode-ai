"""Row826 Self-Regulated Learning - Manages own learning.
Supplied study plan/actual minutes comparison only. Rows(label,planned1..1440,
actual0..1440),1..32. Return signed actual-minus-plan variances and exact
aggregate actual/planned fraction. No evaluation of effective study.
NOT_CLAIMED: actual self-regulation, study effectiveness, verified effort,
learning outcomes, plan enforcement or external effects.
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


def declared_study_variances(rows):
    _rows(rows,'study',32,3)
    for label,planned,actual in rows:_label(label);_integer(planned,1,1440);_integer(actual,0,1440)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('study labels must be unique')
    from fractions import Fraction
    return {'variances':[(label,actual-planned) for label,planned,actual in sorted(rows,key=lambda r:r[0])],
            'actual_to_plan':Fraction(sum(a for _,_,a in rows),sum(p for _,p,_ in rows)),'learning_evaluated':False}
