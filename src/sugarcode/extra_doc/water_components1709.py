"""Water Footprinting.

PARTIAL: caller component water-quantity ledger only, not water footprinting,
verified consumption, hydrology, scarcity assessment or environmental advice.
Caller category quantities are abstract, not verified footprint inventories.
"""
SCOPE='caller component water-quantity ledger only; no verified water footprint claims'


def components(rows):
    """Exactlist/tuple1..64 quads(label,component A,B,C);printable Unicode
    exactstr labels1..40,repeats aggregate;exactint quantities0..1000000.
    Sorted(label,A sum,B sum,C sum,total),aggregate component totals and total.
    Mixedrows accepted;no blue/green/grey definitions,water quality,units,
    geography,time,boundary completeness or physical consumption inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,first,second,third=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(first) is not int or type(second) is not int or type(third) is not int or not 0<=first<=1000000 or not 0<=second<=1000000 or not 0<=third<=1000000:raise ValueError('quantities must be exactint0..1000000')
        a,b,c=groups.get(label,(0,0,0));groups[label]=(a+first,b+second,c+third)
    result=tuple((label,a,b,c,a+b+c) for label,(a,b,c) in sorted(groups.items()))
    totals=tuple(sum(row[index] for row in result) for index in (1,2,3))
    return {'components':result,'totals':totals,'total':sum(totals),'scope':SCOPE}
