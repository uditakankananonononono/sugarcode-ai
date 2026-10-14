"""Doc row1762 Political Economy: PARTIAL supplied sector income/cost ledger.

Sectors exact list1..20 tuples(id,revenue,cost), unique nonblank exact str IDs
1..80; revenue/cost exact ints0..1000. Return balances, total revenue/cost/net
and exact revenue shares (None when total0). No macroeconomic or political claim.
"""
from fractions import Fraction


def audit_sectors(sectors):
    if type(sectors) is not list or not 1<=len(sectors)<=20:raise ValueError('sectors must be an exact list with 1..20 entries')
    ids=set()
    for row in sectors:
        if type(row) is not tuple or len(row)!=3:raise ValueError('sector must be an id revenue cost tuple')
        n,r,c=row
        if type(n) is not str or not 1<=len(n)<=80 or not n.strip() or n in ids:raise ValueError('sector IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(n)
        if type(r) is not int or not 0<=r<=1000:raise ValueError('revenue must be an integer in 0..1000')
        if type(c) is not int or not 0<=c<=1000:raise ValueError('cost must be an integer in 0..1000')
    revenue=sum(r for n,r,c in sectors);cost=sum(c for n,r,c in sectors);shares=[]
    for n,r,c in sectors:
        f=Fraction(r,revenue) if revenue else None;shares.append((n,None if f is None else (f.numerator,f.denominator)))
    return {'balances':[(n,r-c) for n,r,c in sectors],'totals':(revenue,cost,revenue-cost),'revenue_shares':shares,'claim':'PARTIAL','economy_validated':False}
