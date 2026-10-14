"""Radiation Therapy Planning.

PARTIAL: caller-declared discrete interval overlap arithmetic only, not radiation
therapy planning, dosimetry, beam geometry, treatment selection or clinical safety.
No patient data, dose or medical constraints inferred.
"""
SCOPE='caller discrete interval overlap only; no dosimetry or treatment planning'


def overlap(rows):
    """Exactlist/tuple1..64 rows(label,start,end), label exactstr printable Unicode
    length1..40 unique; endpoints exactint0..100000 with start<end. Half-open
    intervals [start,end). Return sorted intersecting label pairs with integer
    overlap lengths, union length and maximum simultaneous intervals. Adjacent
    intervals do not overlap. Mixedlist/tuple rows accepted in either order.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:
        raise ValueError('rows must be exactlist/tuple length1..64')
    parsed=[];labels=set();events={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:
            raise ValueError('row must be exactlist/tuple triple')
        label,start,end=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):
            raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(start) is not int or type(end) is not int or not 0<=start<end<=100000:
            raise ValueError('endpoints must be exactint0..100000 with start<end')
        parsed.append((label,start,end));events[start]=events.get(start,0)+1;events[end]=events.get(end,0)-1
    parsed.sort(key=lambda row:row[0]);pairs=[]
    for i,(label,start,end) in enumerate(parsed):
        for other,lo,hi in parsed[i+1:]:
            length=min(end,hi)-max(start,lo)
            if length>0:pairs.append((label,other,length))
    active=0;peak=0;union=0;previous=None
    for point in sorted(events):
        if previous is not None and active>0:union+=point-previous
        active+=events[point];peak=max(peak,active);previous=point
    return {'pairs':tuple(pairs),'union_length':union,'peak':peak,'scope':SCOPE}
