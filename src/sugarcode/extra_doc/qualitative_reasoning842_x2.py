"""Row842 Qualitative Reasoning - Reasons about qualities.
Supplied signed-direction algebra only. Rows(label,directionA-1..1,
directionB-1..1),1..32. Compose signs by multiplication; report zero,
positive and negative labels. Signs have no external interpretation.
NOT_CLAIMED: qualitative world models, semantic directions, causal truth,
general reasoning, validated observations or external effects.
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


def declared_direction_products(rows):
    _rows(rows,'directions',32,3)
    for label,a,b in rows:_label(label);_integer(a,-1,1);_integer(b,-1,1)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('direction labels must be unique')
    products=[(label,a*b) for label,a,b in sorted(rows)]
    return {'products':products,'positive':[l for l,p in products if p>0],'negative':[l for l,p in products if p<0],'zero':[l for l,p in products if p==0],'interpretation_verified':False}
