"""Row857 Integrative Thinking - Holds tensions.
Supplied two-objective compromise arithmetic only. Rows(label,scoreA0..100,
scoreB0..100),1..32. Rank by largest minimum score,then largest sum,then label.
This declared maximin order does not validate objectives or choose human actions.
NOT_CLAIMED: real integration, tension resolution, relevant objectives,
optimal human choice, decision authority or external effects.
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


def declared_maximin_order(rows):
    _rows(rows,'options',32,3)
    for label,a,b in rows:_label(label);_integer(a,0,100);_integer(b,0,100)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('option labels must be unique')
    order=sorted(rows,key=lambda r:(-min(r[1],r[2]),-(r[1]+r[2]),r[0]))
    return {'order':[l for l,_,_ in order],'integration_evaluated':False}
