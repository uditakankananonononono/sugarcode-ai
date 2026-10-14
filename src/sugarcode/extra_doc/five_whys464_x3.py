"""Row464 5 Whys Analysis - Drills to root cause.
Supplied-data helper only. Rows (label, node 0..31, cause 0..31), 1..32, unique nodes. A node is a root when its cause is itself or is not a listed node. Return per label (sorted) the root node and hop count, or (-1,-1) on a cycle.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: actual root cause, causality, interviews, corrective action or external effects.
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


def analyze_five_whys(rows):
    _rows(rows, 'links', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 31)
        _integer(row[2], 0, 31)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('link labels must be unique')
    if len({row[1] for row in rows}) != len(rows):
        raise ValueError('link nodes must be unique')
    cause={r[1]:r[2] for r in rows}
    out=[]
    for label,node,_ in sorted(rows,key=lambda r:r[0]):
        seen=[node]
        current=node
        while True:
            nxt=cause[current]
            if nxt==current or nxt not in cause:
                out.append((label,current,len(seen)-1))
                break
            if nxt in seen:
                out.append((label,-1,-1))
                break
            seen.append(nxt)
            current=nxt
    return {'chains':out,'root_cause_verified':False}
