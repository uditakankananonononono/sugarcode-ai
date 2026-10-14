"""Exact dual decomposition for separable quadratic with one weighted equality.
NOT_CLAIMED: arbitrary optimization; distributed infrastructure; real-world
model validity; external effects; runtime integration.
"""
from fractions import Fraction
import math


def solve(diagonal,linear,coupling,total):
    if type(diagonal) is not list or not 1<=len(diagonal)<=20:raise ValueError('1..20 separable blocks before scan')
    n=len(diagonal)
    def number(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded decomposition number')
        return Fraction(str(v))
    def vector(v,lo,hi):
        if type(v) is not list or len(v)!=n:raise ValueError('one value per separable block')
        return [number(z,lo,hi) for z in v]
    a=vector(diagonal,.000001,1000);b=vector(linear,-1000,1000);c=vector(coupling,-1000,1000);target=number(total,-1000,1000)
    if all(v==0 for v in c):raise ValueError('at least one nonzero coupling coefficient')
    curvature=sum(z*z/q for z,q in zip(c,a));multiplier=(sum(z*r/q for z,r,q in zip(c,b,a))-target)/curvature
    x=[(r-multiplier*z)/q for r,z,q in zip(b,c,a)]
    block_cost=[q*v*v/2-r*v for q,r,v in zip(a,b,x)]
    primal=sum(block_cost);dual=-sum((r-multiplier*z)**2/(2*q) for r,z,q in zip(b,c,a))-multiplier*target
    residual=sum(z*v for z,v in zip(c,x))-target
    return {'point_fraction':[str(v) for v in x],'multiplier_fraction':str(multiplier),'block_cost_fraction':[str(v) for v in block_cost],
            'primal_objective_fraction':str(primal),'dual_bound_fraction':str(dual),'duality_gap_fraction':str(primal-dual),
            'coupling_residual_fraction':str(residual),'dual_curvature_fraction':str(curvature),
            'method':'exact independent quadratic block argmins with shared dual multiplier',
            'objective_definition':'sum(0.5*a_i*x_i^2 - b_i*x_i), sum(c_i*x_i)=total','external_effects':[]}
