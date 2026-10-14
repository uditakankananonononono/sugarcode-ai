"""Exact Frank-Wolfe on supplied simplex diagonal quadratic.
NOT_CLAIMED: arbitrary constraints, authentic objective, finite-budget optimum,
scalability, external execution or runtime integration.
"""
from fractions import Fraction as F
import math


def optimize(diagonal,linear,initial,iterations,tolerance):
    if type(iterations) is not int or not 1<=iterations<=30:raise ValueError('strict Frank-Wolfe iterations 1..30')
    if type(initial) is not list or not 1<=len(initial)<=8:raise ValueError('1..8 simplex coordinates before scan')
    n=len(initial)
    def num(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded Frank-Wolfe number')
        return F(str(v))
    def vector(row,lo,hi):
        if type(row) is not list or len(row)!=n:raise ValueError('one simplex value per dimension')
        return [num(v,lo,hi) for v in row]
    a=vector(diagonal,.000001,1000);b=vector(linear,-1000,1000);x=vector(initial,0,1);tol=num(tolerance,.000000001,1)
    if sum(x)!=1:raise ValueError('exact simplex coordinate sum must equal one')
    def loss(v):return sum(q*z*z/2+c*z for q,c,z in zip(a,b,v))
    def oracle(v):
        g=[q*z+c for q,c,z in zip(a,b,v)];j=min(range(n),key=lambda j:(g[j],j));direction=[F(int(i==j))-z for i,z in enumerate(v)]
        gap=-sum(v*q for v,q in zip(direction,g));return g,j,direction,gap
    trace=[];history=[str(loss(x))]
    for _ in range(iterations):
        g,j,d,gap=oracle(x)
        if gap<=tol:break
        curvature=sum(q*v*v for q,v in zip(a,d));alpha=min(F(1),gap/curvature);x=[z+alpha*v for z,v in zip(x,d)]
        trace.append({'gradient_fraction':[str(v) for v in g],'vertex_index':j,'direction_fraction':[str(v) for v in d],'gap_fraction':str(gap),'step_fraction':str(alpha),'point_fraction':[str(v) for v in x]})
        history.append(str(loss(x)))
    gap=oracle(x)[-1]
    return {'point_fraction':[str(v) for v in x],'objective_history_fraction':history,'steps':trace,'gap_fraction':str(gap),
            'converged_gap_tolerance':gap<=tol,'iterations_used':len(trace),'global_optimum_claimed':False,'external_effects':[]}
