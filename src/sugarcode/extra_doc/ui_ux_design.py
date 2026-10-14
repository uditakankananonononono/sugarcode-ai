"""Row 287 UI/UX Design: exact bounded UI-slot assignment optimization.

Assigns supplied actions to UI slots minimizing measured weighted interaction
cost, respecting supplied action/slot incompatibilities. Returns a global
finite optimum and an exhaustive candidate count, not a rendered UI.
NOT_CLAIMED: universal usability, visual design, accessibility certification,
user-study validation, aesthetic quality, or autonomous deployment.
"""
from fractions import Fraction
from itertools import permutations


def _number(v):
    if type(v) not in (int,Fraction):raise TypeError('numbers must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('numbers must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('numbers must fit 32 bits')
    return Fraction(v)


def optimize_ui_slots(weights, costs, forbidden=()):
    if type(weights) not in (list,tuple) or type(costs) not in (list,tuple) or type(forbidden) not in (list,tuple):
        raise TypeError('inputs must be lists or tuples')
    n=len(weights)
    if not 1<=n<=8:raise ValueError('action count must be between 1 and 8')
    if len(costs)!=n:raise ValueError('cost matrix must be square and match actions')
    if len(forbidden)>64:raise ValueError('forbidden pair count must not exceed 64')
    for row in costs:
        if type(row) not in (list,tuple) or len(row)!=n:
            raise ValueError('cost matrix must be square and match actions')
    for pair in forbidden:
        if type(pair) not in (list,tuple) or len(pair)!=2:
            raise ValueError('forbidden pairs must contain action and slot indices')
        if any(type(i) is not int or not 0<=i<n for i in pair):
            raise ValueError('forbidden indices must be nonbool integers inside action range')
    w=[_number(v) for v in weights];c=[[_number(v) for v in row] for row in costs]
    if any(v<0 for v in w) or any(v<0 for row in c for v in row):
        raise ValueError('weights and costs must be nonnegative')
    blocked={tuple(pair) for pair in forbidden};best=None;feasible=0
    for assignment in permutations(range(n)):
        if any((i,j) in blocked for i,j in enumerate(assignment)):continue
        feasible+=1
        contributions=[w[i]*c[i][j] for i,j in enumerate(assignment)]
        total=sum(contributions,Fraction(0))
        if best is None or total<best[0]:best=(total,assignment,contributions)
    if best is None:raise ValueError('no feasible UI assignment exists')
    total,assignment,contributions=best
    return {'slots_by_action':list(assignment),'weighted_cost':total,
            'action_costs':contributions,'feasible_assignment_count':feasible,
            'global_finite_optimum':True,'usability_validated':False}
