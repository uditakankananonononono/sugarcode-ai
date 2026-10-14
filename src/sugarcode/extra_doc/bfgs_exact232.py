"""Exact Hessian-BFGS updates on positive diagonal quadratic objectives.
NOT_CLAIMED: unknown objectives; nonlinear convergence; true learned Hessian;
runtime integration, authentic model or external effects.
"""
from fractions import Fraction as F
import math


def optimize(diagonal,linear,initial,iterations):
    if type(iterations) is not int or not 1<=iterations<=10:raise ValueError('strict BFGS iterations 1..10')
    if type(initial) is not list or not 1<=len(initial)<=4:raise ValueError('1..4 BFGS coordinates before scan')
    n=len(initial)
    def vector(row,lo):
        if type(row) is not list or len(row)!=n:raise ValueError('one BFGS value per dimension')
        if any(type(v) not in (int,float) or not lo<=v<=100 or not math.isfinite(v) for v in row):raise ValueError('strict finite bounded BFGS number')
        return [F(str(v)) for v in row]
    a=vector(diagonal,.001);b=vector(linear,-100);x=vector(initial,-100)
    h=[[F(int(i==j)) for j in range(n)] for i in range(n)];trace=[]
    def grad(v):return [q*z+c for q,z,c in zip(a,v,b)]
    def loss(v):return sum(q*z*z/2+c*z for q,z,c in zip(a,v,b))
    history=[str(loss(x))]
    for t in range(iterations):
        g=grad(x)
        if all(v==0 for v in g):break
        aug=[row[:]+[-v] for row,v in zip(h,g)]
        for k in range(n):
            pivot=aug[k][k];aug[k]=[v/pivot for v in aug[k]]
            for i in range(n):
                if i!=k:
                    factor=aug[i][k];aug[i]=[u-factor*v for u,v in zip(aug[i],aug[k])]
        p=[row[-1] for row in aug];alpha=-sum(v*z for v,z in zip(g,p))/sum(q*z*z for q,z in zip(a,p))
        s=[alpha*v for v in p];new=[v+z for v,z in zip(x,s)];y=[q*z for q,z in zip(a,s)];hs=[sum(v*z for v,z in zip(row,s)) for row in h]
        ys=sum(v*z for v,z in zip(y,s));shs=sum(v*z for v,z in zip(s,hs))
        updated=[[h[i][j]+y[i]*y[j]/ys-hs[i]*hs[j]/shs for j in range(n)] for i in range(n)]
        trace.append({'gradient_fraction':[str(v) for v in g],'direction_fraction':[str(v) for v in p],'step_size_fraction':str(alpha),
                      'displacement_fraction':[str(v) for v in s],'gradient_change_fraction':[str(v) for v in y],
                      'hessian_before_fraction':[[str(v) for v in row] for row in h],'hessian_after_fraction':[[str(v) for v in row] for row in updated],
                      'secant_verified':all(sum(updated[i][j]*s[j] for j in range(n))==y[i] for i in range(n))})
        x=new;h=updated;history.append(str(loss(x)))
    return {'point_fraction':[str(v) for v in x],'hessian_fraction':[[str(v) for v in row] for row in h],
            'objective_history_fraction':history,'steps':trace,'iterations_used':len(trace),'stationary':all(v==0 for v in grad(x)),
            'true_hessian_claimed':False,'external_effects':[]}
