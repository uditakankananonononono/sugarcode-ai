"""Wildlife Management.

PARTIAL: caller initial/additions/removals count ledger only, not wildlife
management, population forecasting, ecological assessment or harvest advice.
Caller counts are abstract, not verified animal population measurements.
"""
SCOPE='caller initial-additions-removals count ledger only; no wildlife management advice'


def counts(rows):
    """Exactlist/tuple1..64 quads(label,initial,additions,removals);unique
    printable Unicode exactstr labels1..40;exactint counts0..1000000.
    Sorted(label,final,change),strictly negative final labels,total final
    and total change. Negative results retained to expose caller imbalance.
    Mixedrows accepted;no survival,capacity,time or sustainable harvest inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,initial,additions,removals=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(initial) is not int or type(additions) is not int or type(removals) is not int or not 0<=initial<=1000000 or not 0<=additions<=1000000 or not 0<=removals<=1000000:raise ValueError('counts must be exactint0..1000000')
        change=additions-removals;parsed.append((label,initial+change,change))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'counts':result,'negative':tuple(row[0] for row in result if row[1]<0),'total_final':sum(row[1] for row in result),'total_change':sum(row[2] for row in result),'scope':SCOPE}
