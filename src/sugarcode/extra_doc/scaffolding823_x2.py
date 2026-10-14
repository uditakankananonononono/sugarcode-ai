"""Row823 Scaffolding - Builds progressively.
Supplied prerequisite bitmask checks only. Rows(label,required0..255,
completed0..255),1..32. Report missing bits required &~completed and eligible
labels whose missing mask is zero. No skill completion verification.
NOT_CLAIMED: teaching scaffolds, progressive learning, actual mastery,
prerequisite validity, training execution or external effects.
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


def prerequisite_masks(rows):
    _rows(rows,'stages',32,3)
    for label,required,completed in rows:_label(label);_integer(required,0,255);_integer(completed,0,255)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('stage labels must be unique')
    missing=[(label,required & ~completed) for label,required,completed in sorted(rows)]
    return {'missing':missing,'eligible':[label for label,mask in missing if mask==0],'mastery_verified':False}
