"""Exact finite-box MILP with integer axes and one continuous axis.
NOT_CLAIMED: unbounded/general MILP; many continuous axes; arbitrary nonlinear
objective; authentic constraints; real-world execution; runtime integration.
"""
from fractions import Fraction
from itertools import product
import math


def solve(integer_bounds,continuous_bounds,objective,constraints,direction):
    if type(direction) is not str or direction not in ('min','max'):raise ValueError('mixed direction min or max')
    if type(integer_bounds) is not list or not 1<=len(integer_bounds)<=3:raise ValueError('1..3 integer dimensions before scan')
    n=len(integer_bounds);ranges=[];count=1
    for pair in integer_bounds:
        if type(pair) is not list or len(pair)!=2 or any(type(v) is not int or not -50<=v<=50 for v in pair):raise ValueError('strict integer bound pairs within -50..50')
        lo,hi=pair
        if lo>hi:raise ValueError('ordered inclusive integer bounds')
        count*=hi-lo+1
        if count>1000:raise ValueError('at most 1000 integer assignments before scan')
        ranges.append(range(lo,hi+1))
    def num(v):
        if type(v) not in (int,float) or not -1000<=v<=1000 or not math.isfinite(v):raise ValueError('strict finite mixed value within -1000..1000')
        return Fraction(str(v))
    if type(continuous_bounds) is not list or len(continuous_bounds)!=2:raise ValueError('one continuous bound pair')
    lo,hi=[num(v) for v in continuous_bounds]
    if lo>hi:raise ValueError('ordered inclusive continuous bounds')
    def vector(v):
        if type(v) is not list or len(v)!=n+1:raise ValueError('one coefficient per integer and continuous axis')
        return [num(q) for q in v]
    obj=vector(objective)
    if type(constraints) is not list or len(constraints)>20:raise ValueError('0..20 mixed constraints before scan')
    cons=[]
    for row in constraints:
        if type(row) is not dict or set(row)!={'coefficients','relation','rhs'}:raise ValueError('exact mixed coefficients/relation/rhs fields')
        relation=row['relation']
        if type(relation) is not str or relation not in ('<=','>=','=='):raise ValueError('mixed constraint relation <=, >= or ==')
        cons.append((vector(row['coefficients']),relation,num(row['rhs'])))
    best=None;bestvalue=None;feasible=0
    for ints in product(*ranges):
        left,right=lo,hi;ok=True
        for coeff,relation,rhs in cons:
            rem=rhs-sum(c*x for c,x in zip(coeff[:-1],ints));a=coeff[-1]
            if not a:
                if not (0<=rem if relation=='<=' else 0>=rem if relation=='>=' else rem==0):ok=False;break
            elif relation=='==':left=max(left,rem/a);right=min(right,rem/a)
            elif (relation=='<=' and a>0) or (relation=='>=' and a<0):right=min(right,rem/a)
            else:left=max(left,rem/a)
        if not ok or left>right:continue
        feasible+=1
        y=left if obj[-1]==0 or (obj[-1]>0)==(direction=='min') else right
        point=tuple(map(Fraction,ints))+(y,);value=sum(c*x for c,x in zip(obj,point))
        if best is None or (value<bestvalue if direction=='min' else value>bestvalue):best,bestvalue=point,value
    return {'status':'optimal_in_declared_mixed_box' if best else 'infeasible_in_declared_mixed_box',
            'point_fraction':[str(v) for v in best] if best else None,'objective_fraction':str(bestvalue) if best else None,
            'integer_assignments_checked':count,'feasible_integer_assignments':feasible,'continuous_axes':1,
            'tie_break':'lexicographically smallest full point','global_unbounded_optimum_claimed':False,'external_effects':[]}
