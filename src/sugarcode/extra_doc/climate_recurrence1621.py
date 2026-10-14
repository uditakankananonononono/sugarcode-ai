"""Climate Modeling.

PARTIAL: caller scalar affine recurrence arithmetic only, not climate modeling,
physical simulation,forecasting or validated temperature dynamics. Initial state,
coefficients and forcing are caller abstractions,not calibrated climate data.
"""
from fractions import Fraction
SCOPE='caller scalar affine recurrence only; no climate modeling or forecasts'


def evolve(forcing,initial,num,den):
    """Forcing exactlist/tuple1..64 exactint-1000000..1000000;initial same int
    range;coefficient numerator exactint0..1000,denominator exactint1..1000,
    num<=den. Exact states next=(num/den)*previous+forcing. Return initial plus
    every next state and final state. No physical units/stability claims or
    inferred parameter values. Preserve input order;no missing steps inferred.
    """
    if type(initial) is not int or not -1000000<=initial<=1000000:raise ValueError('initial must be exactint-1000000..1000000')
    if type(num) is not int or type(den) is not int or not 0<=num<=den<=1000 or den==0:raise ValueError('coefficient must be exactint0<=num<=den<=1000 and den>0')
    if type(forcing) not in (list,tuple) or not 1<=len(forcing)<=64:raise ValueError('forcing must be exactlist/tuple length1..64')
    for value in forcing:
        if type(value) is not int or not -1000000<=value<=1000000:raise ValueError('forcing value must be exactint-1000000..1000000')
    coefficient=Fraction(num,den);state=Fraction(initial);states=[state]
    for value in forcing:state=coefficient*state+value;states.append(state)
    return {'states':tuple(states),'final':state,'scope':SCOPE}
