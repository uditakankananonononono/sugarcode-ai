"""Row 332 Aerospace Design: exact finite static thrust-margin concept selection.

Chooses one supplied component option (mass,thrust,cost) per category to
minimize cost while total thrust meets supplied acceleration times total mass
including payload. Computes exact static thrust surplus, no trajectory model.
Caps six categories/four choices/4096 concepts and 32-bit input rationals.
NOT_CLAIMED: flightworthiness, orbital capability, aerodynamic stability,
structural safety, actual aircraft/spacecraft fabrication or deployment.
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


def thrust_concept(components,payload,required_acceleration):
    if type(components) not in (list,tuple):raise TypeError('components must be a list or tuple')
    if not 1<=len(components)<=6:raise ValueError('category count must be between 1 and 6')
    for options in components:
        if type(options) not in (list,tuple) or not 1<=len(options)<=4:
            raise ValueError('each category must have between 1 and 4 options')
        if any(type(option) not in (list,tuple) or len(option)!=3 for option in options):
            raise ValueError('options must contain mass thrust and cost')
    load=_number(payload);acc=_number(required_acceleration)
    if load<0:raise ValueError('payload must be nonnegative')
    if acc<=0:raise ValueError('required_acceleration must be positive')
    data=[[tuple(_number(v) for v in option) for option in options] for options in components]
    if any(v<0 for options in data for option in options for v in option):
        raise ValueError('mass thrust and cost must be nonnegative')
    best=None;feasible=0
    for indices in product(*(range(len(options)) for options in data)):
        chosen=[data[i][j] for i,j in enumerate(indices)]
        mass=load+sum((v[0] for v in chosen),Fraction(0));thrust=sum((v[1] for v in chosen),Fraction(0))
        surplus=thrust-acc*mass
        if surplus<0:continue
        feasible+=1;cost=sum((v[2] for v in chosen),Fraction(0))
        if best is None or cost<best[0]:best=(cost,indices,mass,thrust,surplus)
    if best is None:raise ValueError('no concept meets static thrust requirement')
    cost,indices,mass,thrust,surplus=best
    return {'option_indices':list(indices),'total_mass':mass,'total_thrust':thrust,
            'thrust_surplus':surplus,'cost':cost,'feasible_count':feasible,'flightworthiness_validated':False}
