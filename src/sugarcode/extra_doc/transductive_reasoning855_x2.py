"""Row855 Transductive Reasoning - Reasons from specific to specific.
Supplied one-dimensional nearest labeled exemplar only. Rows(label,coordinate
-1000..1000,class_code0..15),1..32;query-1000..1000. Return all equally nearest
exemplar labels sorted and their distinct sorted class codes;no forced tiebreak.
NOT_CLAIMED: valid classification, generalization, meaningful distance,
semantic analogy, real-world prediction or external effects.
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


def nearest_declared_exemplars(rows,query):
    _rows(rows,'exemplars',32,3);_integer(query,-1000,1000)
    for label,coordinate,code in rows:_label(label);_integer(coordinate,-1000,1000);_integer(code,0,15)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('exemplar labels must be unique')
    distance=min(abs(coordinate-query) for _,coordinate,_ in rows)
    nearest=[(label,code) for label,coordinate,code in sorted(rows) if abs(coordinate-query)==distance]
    return {'distance':distance,'exemplars':[l for l,_ in nearest],'class_codes':sorted({c for _,c in nearest}),'classification_verified':False}
