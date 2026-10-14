"""Row 331 Automotive Design: finite vehicle mass-layout concept selection.

Chooses one supplied component option (mass,longitudinal position,cost) per
component; positions lie between front axle0 and rear axle wheelbase. Computes
exact static axle loads from moments, and minimizes cost subject to load caps.
At most six components/four options each/4096 candidate concepts.
NOT_CLAIMED: vehicle safety, crashworthiness, roadworthiness, suspension design,
real-world engineering validation, fabrication or deployment.
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


def vehicle_layout(components,wheelbase,front_cap,rear_cap):
    if type(components) not in (list,tuple):raise TypeError('components must be a list or tuple')
    if not 1<=len(components)<=6:raise ValueError('component count must be between 1 and 6')
    for options in components:
        if type(options) not in (list,tuple) or not 1<=len(options)<=4:
            raise ValueError('each component must have between 1 and 4 options')
        if any(type(option) not in (list,tuple) or len(option)!=3 for option in options):
            raise ValueError('options must contain mass position and cost')
    length=_number(wheelbase);fc=_number(front_cap);rc=_number(rear_cap)
    if length<=0:raise ValueError('wheelbase must be positive')
    if fc<0 or rc<0:raise ValueError('axle caps must be nonnegative')
    data=[[tuple(_number(v) for v in option) for option in options] for options in components]
    if any(m<0 or c<0 or not 0<=x<=length for opts in data for m,x,c in opts):
        raise ValueError('mass cost and positions must be nonnegative and positions within wheelbase')
    best=None;feasible=0
    for indices in product(*(range(len(opts)) for opts in data)):
        selected=[data[i][j] for i,j in enumerate(indices)]
        mass=sum((m for m,x,c in selected),Fraction(0))
        rear=sum((m*x for m,x,c in selected),Fraction(0))/length;front=mass-rear
        if front>fc or rear>rc:continue
        feasible+=1;cost=sum((c for m,x,c in selected),Fraction(0))
        if best is None or cost<best[0]:best=(cost,indices,mass,front,rear)
    if best is None:raise ValueError('no layout satisfies axle caps')
    cost,indices,mass,front,rear=best
    return {'option_indices':list(indices),'total_mass':mass,'front_load':front,'rear_load':rear,
            'cost':cost,'feasible_count':feasible,'roadworthiness_validated':False}
