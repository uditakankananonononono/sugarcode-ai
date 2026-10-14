"""Row848 Probabilistic Reasoning - Reasons under uncertainty.
Supplied nonnegative likelihood-weight normalization only. Rows(label,weight
0..1000000),1..32;at least one positive weight. Return exact Fraction shares
summing to1,sorted by label. Inputs are not verified probabilities.
NOT_CLAIMED: valid beliefs, Bayesian evidence, calibrated uncertainty,
likelihood truth, predictions or external effects.
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


def declared_weight_shares(rows):
    _rows(rows,'weights',32,2)
    for label,weight in rows:_label(label);_integer(weight,0,1000000)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('weight labels must be unique')
    total=sum(w for _,w in rows)
    if total==0:raise ValueError('at least one weight must be positive')
    from fractions import Fraction
    return {'shares':[(label,Fraction(weight,total)) for label,weight in sorted(rows,key=lambda r:r[0])],'beliefs_verified':False}
