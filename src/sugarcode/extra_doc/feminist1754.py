"""Doc row1754 Feminist Theory: PARTIAL supplied category/resource ledger.

Groups exact list2..20 (id,units) tuples; IDs exact nonblank str1..80 unique;
units exact int0..1000. Return exact shares and ordered max/min supplied groups,
max-min gap. No inferred gender, discrimination, fairness or feminist validity.
"""
from fractions import Fraction


def summarize_resources(groups):
    if type(groups) is not list or not 2<=len(groups)<=20:raise ValueError('groups must be an exact list with 2..20 entries')
    ids=set()
    for row in groups:
        if type(row) is not tuple or len(row)!=2:raise ValueError('group must be an id units tuple')
        name,units=row
        if type(name) is not str or not 1<=len(name)<=80 or not name.strip() or name in ids:raise ValueError('group IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(name)
        if type(units) is not int or not 0<=units<=1000:raise ValueError('units must be an integer in 0..1000')
    total=sum(u for n,u in groups);shares=[]
    for n,u in groups:
        share=Fraction(u,total) if total else None
        shares.append((n,None if share is None else (share.numerator,share.denominator)))
    low=min(u for n,u in groups);high=max(u for n,u in groups)
    return {'total':total,'shares':shares,'minimum':[n for n,u in groups if u==low],'maximum':[n for n,u in groups if u==high],'gap':high-low,'claim':'PARTIAL','fairness_validated':False}
