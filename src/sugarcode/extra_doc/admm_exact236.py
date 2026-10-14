"""Exact rational diagonal-quadratic plus L1 ADMM with x=z splitting.
NOT_CLAIMED: arbitrary convex solver; distributed infrastructure; model truth;
finite-budget convergence guarantee; real-world execution; runtime integration.
"""
from fractions import Fraction
import math


def solve(diagonal,linear,penalty,rho,initial,iterations,tolerance):
    if type(iterations) is not int or not 1<=iterations<=30:raise ValueError('strict ADMM iterations 1..30')
    if type(initial) is not list or not 1<=len(initial)<=8:raise ValueError('1..8 ADMM coordinates before scan')
    d=len(initial)
    def number(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded ADMM number')
        return Fraction(str(v))
    def vector(v,lo,hi):
        if type(v) is not list or len(v)!=d:raise ValueError('one ADMM value per coordinate')
        return [number(q,lo,hi) for q in v]
    a=vector(diagonal,.000001,1000);b=vector(linear,-1000,1000);z=vector(initial,-1000,1000)
    lam=number(penalty,0,1000);r=number(rho,.000001,1000);tol=number(tolerance,.000000001,1)
    u=[Fraction(0)]*d;history=[];converged=False
    for t in range(1,iterations+1):
        x=[(v+r*(q-w))/(h+r) for h,v,q,w in zip(a,b,z,u)];old=z[:]
        raw=[q+w for q,w in zip(x,u)];threshold=lam/r
        z=[v-threshold if v>threshold else v+threshold if v<-threshold else Fraction(0) for v in raw]
        u=[w+q-v for w,q,v in zip(u,x,z)]
        primal=max(abs(q-v) for q,v in zip(x,z));dual=r*max(abs(q-v) for q,v in zip(z,old))
        history.append({'step':t,'x_fraction':[str(v) for v in x],'z_fraction':[str(v) for v in z],'scaled_dual_fraction':[str(v) for v in u],'primal_infinity_fraction':str(primal),'dual_infinity_fraction':str(dual)})
        if primal<=tol and dual<=tol:converged=True;break
    objective=sum(h*v*v/2-q*v+lam*abs(v) for h,q,v in zip(a,b,z))
    gradient=[h*v-q for h,v,q in zip(a,z,b)]
    kkt=max(abs(g+lam) if v>0 else abs(g-lam) if v<0 else max(abs(g)-lam,0) for g,v in zip(gradient,z))
    return {'solution_fraction':[str(v) for v in z],'objective_fraction':str(objective),'trace':history,'iterations_used':len(history),
            'converged_residual_tolerance':converged,'kkt_infinity_fraction':str(kkt),'rho_fraction':str(r),'penalty_fraction':str(lam),
            'method':'exact rational diagonal quadratic L1 ADMM','stopping_contract':'absolute infinity primal and dual residuals <= supplied tolerance',
            'global_optimum_claimed':False,'external_effects':[]}
