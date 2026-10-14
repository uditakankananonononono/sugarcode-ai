"""Exact proximal gradient for supplied positive diagonal quadratic plus L1.
NOT_CLAIMED: arbitrary nonsmooth objectives; authentic model; convergence in
all finite budgets; scalable execution or runtime integration.
"""
from fractions import Fraction as F
import math


def optimize(diagonal,linear,penalty,initial,iterations,tolerance):
    if type(iterations) is not int or not 1<=iterations<=50:raise ValueError('strict proximal iterations 1..50')
    if type(initial) is not list or not 1<=len(initial)<=8:raise ValueError('1..8 proximal coordinates before scan')
    n=len(initial)
    def num(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded proximal number')
        return F(str(v))
    def vec(row,lo):
        if type(row) is not list or len(row)!=n:raise ValueError('one proximal value per dimension')
        return [num(v,lo,1000) for v in row]
    a=vec(diagonal,.000001);b=vec(linear,-1000);x=vec(initial,-1000);lam=num(penalty,0,1000);tol=num(tolerance,.000000001,1);rate=1/max(a)
    def loss(v):return sum(q*z*z/2+c*z+lam*abs(z) for q,c,z in zip(a,b,v))
    def residual(v):return [abs(q*z+c+lam) if z>0 else abs(q*z+c-lam) if z<0 else max(abs(c)-lam,F(0)) for q,c,z in zip(a,b,v)]
    history=[str(loss(x))];trace=[]
    for t in range(iterations):
        kkt=residual(x)
        if max(kkt)<=tol:break
        g=[q*z+c for q,c,z in zip(a,b,x)];raw=[z-rate*v for z,v in zip(x,g)];threshold=rate*lam
        new=[v-threshold if v>threshold else v+threshold if v<-threshold else F(0) for v in raw]
        trace.append({'gradient_fraction':[str(v) for v in g],'forward_point_fraction':[str(v) for v in raw],
                      'point_fraction':[str(v) for v in new],'threshold_fraction':str(threshold),'kkt_before_fraction':[str(v) for v in kkt]})
        x=new;history.append(str(loss(x)))
    kkt=residual(x)
    return {'point_fraction':[str(v) for v in x],'objective_history_fraction':history,'steps':trace,'iterations_used':len(trace),
            'step_size_fraction':str(rate),'kkt_fraction':[str(v) for v in kkt],'converged_kkt_tolerance':max(kkt)<=tol,
            'global_optimum_claimed':False,'external_effects':[]}
