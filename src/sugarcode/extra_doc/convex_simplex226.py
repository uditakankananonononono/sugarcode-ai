"""Exact convex positive diagonal quadratic minimization on a scaled simplex.
NOT_CLAIMED: arbitrary convex objective; authentic constraints; real decision;
runtime integration; unbounded-domain optimizer.
"""
from fractions import Fraction
import math
from itertools import combinations


def solve(diagonal,linear,total):
    if type(diagonal) is not list or not 1<=len(diagonal)<=8:raise ValueError('1..8 convex dimensions before scan')
    n=len(diagonal)
    def num(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded convex number')
        return Fraction(str(v))
    a=[num(v,.000001,1000) for v in diagonal]
    if type(linear) is not list or len(linear)!=n:raise ValueError('one linear value per convex dimension')
    b=[num(v,-1000,1000) for v in linear];t=num(total,.000001,1000)
    checked=0;solution=None;multiplier=None
    for size in range(1,n+1):
        for active in combinations(range(n),size):
            checked+=1;lam=(sum(b[i]/a[i] for i in active)-t)/sum(1/a[i] for i in active)
            x=[(b[i]-lam)/a[i] if i in active else Fraction(0) for i in range(n)]
            if any(x[i]<=0 for i in active) or any(b[i]>lam for i in range(n) if i not in active):continue
            solution=x;multiplier=lam;break
        if solution is not None:break
    if solution is None:raise ValueError('no exact active set found')
    gradient=[q*v-c for q,v,c in zip(a,solution,b)];slack=[v+multiplier for v in gradient]
    return {'point_fraction':[str(v) for v in solution],'objective_fraction':str(sum(q*v*v/2-c*v for q,v,c in zip(a,solution,b))),
            'equality_multiplier_fraction':str(multiplier),'nonnegative_multipliers_fraction':[str(v) for v in slack],
            'active_indices':[i for i,v in enumerate(solution) if v>0],'active_sets_checked':checked,
            'sum_fraction':str(sum(solution)),'kkt_verified_in_supplied_model':sum(solution)==t and all(v>=0 for v in slack) and all(x*v==0 for x,v in zip(solution,slack)),
            'scope':'unique exact convex optimum in supplied nonnegative sum-equality quadratic','external_effects':[]}
