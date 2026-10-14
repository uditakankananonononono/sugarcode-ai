"""Doc row1035 Metropolis-Hastings: PARTIAL deterministic acceptance fixture.

Current/proposed target weights exact ints1..100; forward/reverse proposal
weights exact ints1..100 (caller supplies proportional probabilities, not rates).
Draw exact tuple(num,den), nonbool ints0<=num<den<=100. Acceptance probability
min(1,target_new*reverse/(target_old*forward)); accept draw strictly below it.
No proposal generation, stationarity proof, convergence or inference claim.
"""
from fractions import Fraction


def decide(current,proposed,forward,reverse,draw):
    if any(type(x) is not int or not 1<=x<=100 for x in (current,proposed,forward,reverse)):
        raise ValueError('weights must be exact integers in 1..100')
    if type(draw) is not tuple or len(draw)!=2 or any(type(x) is not int for x in draw) or not 0<=draw[0]<draw[1]<=100:
        raise ValueError('draw must be an exact integer fraction with 0<=num<den<=100')
    probability=min(Fraction(1),Fraction(proposed*reverse,current*forward))
    return {'probability':(probability.numerator,probability.denominator),'accepted':Fraction(*draw)<probability,
            'claim':'PARTIAL','stationarity_validated':False}
