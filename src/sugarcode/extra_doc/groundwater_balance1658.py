"""Groundwater Management.

PARTIAL: caller initial/recharge/withdrawal balance only, not groundwater
management, aquifer modeling, sustainable yield or ecological assessment.
Caller compatible quantities are not verified hydrological measurements.
"""
SCOPE='caller initial-recharge-withdrawal balances only; no groundwater management advice'


def balances(rows):
    """Exactlist/tuple1..64 quads(label,initial,recharge,withdrawal);unique
    printable Unicode exactstr labels1..40;exactint quantities0..1000000.
    Sorted(label,initial+recharge-withdrawal,recharge-withdrawal),strictly
    negative final-balance labels,total final and total change. Negative
    results not clamped. Mixedrows accepted;no time,area,porosity or limits.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple quadruple')
        label,initial,recharge,withdrawal=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(initial) is not int or type(recharge) is not int or type(withdrawal) is not int or not 0<=initial<=1000000 or not 0<=recharge<=1000000 or not 0<=withdrawal<=1000000:raise ValueError('quantities must be exactint0..1000000')
        change=recharge-withdrawal;parsed.append((label,initial+change,change))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'balances':result,'negative':tuple(row[0] for row in result if row[1]<0),'total_final':sum(row[1] for row in result),'total_change':sum(row[2] for row in result),'scope':SCOPE}
