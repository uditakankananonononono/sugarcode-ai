"""Row847 Counterfactual Reasoning - Reasons about alternatives.
Supplied linear arithmetic scenario perturbations only. Rows(label,base_input
-100..100,alternative_input same,slope-100..100,intercept-100..100),1..32.
Return baseline and alternative slope*x+intercept and their difference.
NOT_CLAIMED: real counterfactuals, causal structure, model truth, feasible
alternatives, predictions, advice or external effects.
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


def declared_linear_alternatives(rows):
    _rows(rows,'scenarios',32,5)
    for label,base,alternative,slope,intercept in rows:
        _label(label)
        for value in (base,alternative,slope,intercept):_integer(value,-100,100)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('scenario labels must be unique')
    return {'alternatives':[(label,slope*base+intercept,slope*alternative+intercept,slope*(alternative-base)) for label,base,alternative,slope,intercept in sorted(rows)],'counterfactuals_verified':False}
