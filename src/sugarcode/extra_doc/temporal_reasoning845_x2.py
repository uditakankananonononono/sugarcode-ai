"""Row845 Temporal Reasoning - Reasons about time.
Supplied half-open interval overlap arithmetic only. Rows(label,start0..1000000,
end0..1000000),1..32;start<end. Return sorted intersecting label pairs and
positive overlap durations. Adjacent endpoints do not overlap.
NOT_CLAIMED: actual event timing, calendar availability, causal time order,
timezone interpretation, scheduling execution or external effects.
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


def declared_interval_overlaps(rows):
    _rows(rows,'intervals',32,3)
    for label,start,end in rows:
        _label(label);_integer(start,0,1000000);_integer(end,0,1000000)
        if start>=end:raise ValueError('start must precede end')
    if len({r[0] for r in rows})!=len(rows):raise ValueError('interval labels must be unique')
    ordered=sorted(rows,key=lambda r:r[0]);overlaps=[]
    for i,(a,sa,ea) in enumerate(ordered):
        for b,sb,eb in ordered[i+1:]:
            duration=min(ea,eb)-max(sa,sb)
            if duration>0:overlaps.append((a,b,duration))
    return {'overlaps':overlaps,'events_verified':False}
