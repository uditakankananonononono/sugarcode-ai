"""Forestry.

PARTIAL: caller initial/planted/lost area ledger only, not forestry,
forest growth, habitat assessment, carbon accounting or harvest advice.
Caller areas are abstract compatible units, not verified forest measurements.
"""
SCOPE='caller initial-planted-lost area ledger only; no forestry advice'


def areas(rows):
    """Exactlist/tuple1..64 quads(label,initial,planted,lost);unique printable
    Unicode exactstr labels1..40;exactint areas0..1000000. Sorted(label,final,
    change),strictly negative final labels,total final and total change.
    Negative balances retained. Mixedrows accepted;no density,age,overlap,
    regeneration,species or ecosystem effects inferred from area arithmetic.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,initial,planted,lost=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(initial) is not int or type(planted) is not int or type(lost) is not int or not 0<=initial<=1000000 or not 0<=planted<=1000000 or not 0<=lost<=1000000:raise ValueError('areas must be exactint0..1000000')
        change=planted-lost;parsed.append((label,initial+change,change))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'areas':result,'negative':tuple(row[0] for row in result if row[1]<0),'total_final':sum(row[1] for row in result),'total_change':sum(row[2] for row in result),'scope':SCOPE}
