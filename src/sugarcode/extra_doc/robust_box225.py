"""Exact robust finite-menu choice with independent coefficient box uncertainty.
NOT_CLAIMED: global continuous optimum; authentic uncertainty sets; actual
outside-set performance; real-world execution; runtime integration.
"""
from fractions import Fraction
import math


def choose(options,nominal,radius,constraints):
    if type(nominal) is not list or not 1<=len(nominal)<=8:raise ValueError('1..8 robust dimensions before scan')
    d=len(nominal)
    def num(v,lo,hi):
        if type(v) not in (int,float) or not lo<=v<=hi or not math.isfinite(v):raise ValueError('strict finite bounded robust number')
        return Fraction(str(v))
    def vector(v,lo,hi):
        if type(v) is not list or len(v)!=d:raise ValueError('one robust value per dimension')
        return [num(q,lo,hi) for q in v]
    c=vector(nominal,-1000,1000);r=vector(radius,0,1000)
    if type(constraints) is not list or len(constraints)>20:raise ValueError('0..20 robust constraints before scan')
    cons=[]
    for row in constraints:
        if type(row) is not dict or set(row)!={'nominal','radius','rhs'}:raise ValueError('exact robust nominal/radius/rhs fields')
        cons.append((vector(row['nominal'],-1000,1000),vector(row['radius'],0,1000),num(row['rhs'],-1000,1000)))
    if type(options) is not list or not 1<=len(options)<=100:raise ValueError('1..100 robust options before scan')
    seen=set();scores=[]
    for row in options:
        if type(row) is not dict or set(row)!={'id','point'}:raise ValueError('exact robust id/point fields')
        ident=row['id']
        if type(ident) is not str or not 1<=len(ident)<=120 or not ident.strip() or ident in seen:raise ValueError('unique nonblank robust ids 1..120')
        seen.add(ident);x=vector(row['point'],-1000,1000)
        worst=sum(a*v+b*abs(v) for a,b,v in zip(c,r,x));best=sum(a*v-b*abs(v) for a,b,v in zip(c,r,x))
        lhs=[sum(a*v+b*abs(v) for a,b,v in zip(nom,rad,x)) for nom,rad,rhs in cons];slack=[rhs-v for v,(nom,rad,rhs) in zip(lhs,cons)]
        feasible=all(v>=0 for v in slack)
        scores.append({'id':ident,'worst_objective_fraction':str(worst),'best_objective_fraction':str(best),'worst_constraint_lhs_fraction':[str(v) for v in lhs],'robust_slack_fraction':[str(v) for v in slack],'robust_feasible_in_supplied_boxes':feasible,
                       'adversarial_objective_coefficients_fraction':[str(a+b if v>=0 else a-b) for a,b,v in zip(c,r,x)]})
    feasible=[s for s in scores if s['robust_feasible_in_supplied_boxes']]
    best=min(feasible,key=lambda s:(Fraction(s['worst_objective_fraction']),s['id'])) if feasible else None
    return {'selected_id':best['id'] if best else None,'status':'minimax_in_supplied_robust_menu' if best else 'no_robust_feasible_option','scores':scores,
            'uncertainty_set':'independent closed coefficient boxes, separate objective and constraint boxes','external_effects':[]}
