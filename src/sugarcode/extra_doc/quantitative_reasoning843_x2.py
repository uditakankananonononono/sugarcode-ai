"""Row843 Quantitative Reasoning - Reasons about quantities.
Supplied unit-scale conversion arithmetic only. Rows(label,quantity-1000..1000,
source_scale1..1000,target_scale1..1000),1..32. Return exact Fraction
quantity*source_scale/target_scale. Scales are caller declared, not units verified.
NOT_CLAIMED: valid units, dimensional consistency, measurement truth,
general quantitative reasoning, financial advice or external effects.
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


def declared_scale_conversions(rows):
    _rows(rows,'quantities',32,4)
    for label,quantity,source,target in rows:_label(label);_integer(quantity,-1000,1000);_integer(source,1,1000);_integer(target,1,1000)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('quantity labels must be unique')
    from fractions import Fraction
    return {'converted':[(label,Fraction(quantity*source,target)) for label,quantity,source,target in sorted(rows,key=lambda r:r[0])],'units_verified':False}
