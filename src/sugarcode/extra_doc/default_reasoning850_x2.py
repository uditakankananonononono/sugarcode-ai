"""Row850 Default Reasoning - Assumes unless contradicted.
Supplied positive default/contradiction bit checklist only. Rows(label,default
bool,contradicted bool),1..32. Accept default iff declared true and not
contradicted,report blocked defaults and inactive labels separately.
NOT_CLAIMED: defensible assumptions, knowledge truth, contradiction detection,
real-world default reasoning, decisions or external effects.
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


def declared_default_bits(rows):
    _rows(rows,'defaults',32,3)
    for label,default,contradicted in rows:
        _label(label)
        if type(default) is not bool or type(contradicted) is not bool:raise TypeError('default flags must be exact bool')
    if len({r[0] for r in rows})!=len(rows):raise ValueError('default labels must be unique')
    return {'accepted':[l for l,d,c in sorted(rows) if d and not c],
            'blocked':[l for l,d,c in sorted(rows) if d and c],'inactive':[l for l,d,c in sorted(rows) if not d],'assumptions_verified':False}
