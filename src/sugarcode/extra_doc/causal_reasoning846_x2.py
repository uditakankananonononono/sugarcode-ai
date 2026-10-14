"""Row846 Causal Reasoning - Reasons about causes.
Supplied observational two-group binary count arithmetic only. Rows(label,
treated_success0..100,treated_total1..100,control_success0..100,control_total
1..100),1..32;success<=total. Return exact treated-minus-control proportions.
NOT_CLAIMED: causal identification, randomized assignment, valid controls,
confounder adjustment, treatment advice or external effects.
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


def observed_group_differences(rows):
    _rows(rows,'groups',32,5)
    for label,ts,tn,cs,cn in rows:
        _label(label);_integer(ts,0,100);_integer(tn,1,100);_integer(cs,0,100);_integer(cn,1,100)
        if ts>tn or cs>cn:raise ValueError('successes must not exceed group totals')
    if len({r[0] for r in rows})!=len(rows):raise ValueError('group labels must be unique')
    from fractions import Fraction
    return {'differences':[(label,Fraction(ts,tn)-Fraction(cs,cn)) for label,ts,tn,cs,cn in sorted(rows,key=lambda r:r[0])],'causality_identified':False}
