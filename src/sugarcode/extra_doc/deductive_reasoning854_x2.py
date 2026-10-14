"""Row854 Deductive Reasoning - Derives from general.
Supplied truth-table logical implication only. Rows(label,premise0..1,
conclusion0..1),1..32. Report material implication false only for(1,0) and
contrapositive truth, both sorted. Inputs are declared bits, not propositions.
NOT_CLAIMED: real proof validity, sound premises, semantic propositions,
general deduction, knowledge truth or external effects.
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


def declared_material_implications(rows):
    _rows(rows,'statements',32,3)
    for label,premise,conclusion in rows:_label(label);_integer(premise,0,1);_integer(conclusion,0,1)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('statement labels must be unique')
    return {'truths':[(label,not bool(premise) or bool(conclusion),bool(conclusion) or not bool(premise)) for label,premise,conclusion in sorted(rows,key=lambda r:r[0])],'proofs_verified':False}
