"""Row859 Design Thinking - Creates solutions.
Supplied prototype binary requirement-mask filter only. Rows(label,coverage
0..255,effort0..1000),1..32;required0..255. Return covering prototypes ordered
by fewest extra covered bits,then effort,then label. No actual design creation.
NOT_CLAIMED: useful designs, validated needs, user research, creativity,
optimal real solutions, prototype execution or external effects.
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


def declared_prototype_screen(rows,required):
    _rows(rows,'prototypes',32,3);_integer(required,0,255)
    for label,coverage,effort in rows:_label(label);_integer(coverage,0,255);_integer(effort,0,1000)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('prototype labels must be unique')
    eligible=[(label,(coverage & ~required).bit_count(),effort) for label,coverage,effort in rows if coverage & required==required]
    return {'prototypes':sorted(eligible,key=lambda r:(r[1],r[2],r[0])),'designs_validated':False}
