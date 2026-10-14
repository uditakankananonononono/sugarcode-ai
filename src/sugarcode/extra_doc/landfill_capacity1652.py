"""Landfill Management.

PARTIAL: caller capacity/used/incoming ledger only, not landfill management,
site engineering, leachate control, safety assessment or regulatory compliance.
Quantities are caller-defined compatible units, not verified site measurements.
"""
SCOPE='caller capacity-used-incoming ledger only; no landfill management advice'


def capacity(rows):
    """Exactlist/tuple1..64 quads(label,capacity,used,incoming);unique printable
    Unicode exactstr labels1..40;exactint0<=used<=capacity<=1000000,incoming
    exactint0..1000000. Sorted(label,free before,free after),strictly overflowing
    labels and total signed free-after. Negative remainder is not clamped.
    Mixedrows accepted;no construction,settlement,permits or hazard assumptions.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,limit,used,incoming=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(limit) is not int or type(used) is not int or type(incoming) is not int or not 0<=used<=limit<=1000000 or not 0<=incoming<=1000000:raise ValueError('quantities must be exactint0<=used<=capacity<=1000000 and incoming0..1000000')
        free=limit-used;parsed.append((label,free,free-incoming))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'capacity':result,'overflow':tuple(row[0] for row in result if row[2]<0),'total_free_after':sum(row[2] for row in result),'scope':SCOPE}
