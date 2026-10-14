"""Row852 Abductive Reasoning - Infers best explanation.
Supplied hypothesis positive evidence mask0..255 and nonnegative cost0..100
only. Rows(label,coverage_mask,cost),1..32;observed_mask0..255. Return
hypotheses covering all observed bits, ranked cost ascending then label.
NOT_CLAIMED: real explanations, causal validity, hypothesis truth, best
scientific inference, decisions or external effects.
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


def declared_covering_hypotheses(rows,observed):
    _rows(rows,'hypotheses',32,3);_integer(observed,0,255)
    for label,coverage,cost in rows:_label(label);_integer(coverage,0,255);_integer(cost,0,100)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('hypothesis labels must be unique')
    eligible=[(label,cost) for label,coverage,cost in rows if coverage & observed==observed]
    return {'covering':sorted(eligible,key=lambda r:(r[1],r[0])),'explanations_verified':False}
