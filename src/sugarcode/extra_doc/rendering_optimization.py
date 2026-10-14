"""Row 294 Rendering Optimization: exact finite quality/time allocation.

Chooses one supplied render mode per scene component to maximize total
quality under a rational time budget. Enumerates at most 4096 allocations;
equal quality prefers lower time, then first supplied product-order tuple.
NOT_CLAIMED: actual renderer execution, perceptual quality measurement,
mode cost prediction, global scene realism or automatic deployment.
"""
from fractions import Fraction
from itertools import product


def _number(v):
    if type(v) not in (int,Fraction):raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('values must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('values must fit 32 bits')
    return Fraction(v)


def allocate_render_modes(components,time_budget):
    if type(components) not in (list,tuple):raise TypeError('components must be a list or tuple')
    if not 1<=len(components)<=6:raise ValueError('component count must be between 1 and 6')
    for modes in components:
        if type(modes) not in (list,tuple) or not 1<=len(modes)<=4:
            raise ValueError('each component must have between 1 and 4 modes')
    for modes in components:
        for mode in modes:
            if type(mode) not in (list,tuple) or len(mode)!=2:
                raise ValueError('modes must contain time and quality')
    budget=_number(time_budget)
    data=[[(_number(t),_number(q)) for t,q in modes] for modes in components]
    if budget<0:raise ValueError('time budget must be nonnegative')
    if any(t<0 or q<0 for modes in data for t,q in modes):
        raise ValueError('mode time and quality must be nonnegative')
    best=None;feasible=0;candidates=0
    for indices in product(*(range(len(modes)) for modes in data)):
        candidates+=1
        time=sum((data[i][j][0] for i,j in enumerate(indices)),Fraction(0))
        if time>budget:continue
        feasible+=1;quality=sum((data[i][j][1] for i,j in enumerate(indices)),Fraction(0))
        if best is None or quality>best[0] or (quality==best[0] and time<best[1]):
            best=(quality,time,indices)
    if best is None:raise ValueError('no render allocation fits time budget')
    quality,time,indices=best
    return {'mode_indices':list(indices),'total_quality':quality,'total_time':time,
            'budget_slack':budget-time,'candidate_count':candidates,'feasible_count':feasible,
            'renderer_executed':False}
