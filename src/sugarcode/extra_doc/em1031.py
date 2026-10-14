"""Doc row1031 Expectation-Maximization: PARTIAL one-step Bernoulli mixture.

Observations exact list1..50 nonbool integers0/1. Prior mixture weight and two
Bernoulli success probabilities exact tuple(num,den), nonbool ints with
1<=num<den<=100. Compute exact posterior responsibilities then one M step for
mixture and success probabilities. Return normalized rational pairs. No random
fit, convergence, identifiability or fitted model validity claim.
"""
from fractions import Fraction


def step(observations,weight,p1,p2):
    if type(observations) is not list or not 1<=len(observations)<=50:
        raise ValueError('observations must be an exact list with 1..50 entries')
    if any(type(x) is not int or x not in (0,1) for x in observations):
        raise ValueError('observations must be exact integers zero or one')
    params=[]
    for pair in (weight,p1,p2):
        if type(pair) is not tuple or len(pair)!=2 or any(type(x) is not int for x in pair) or not 1<=pair[0]<pair[1]<=100:
            raise ValueError('parameters must be exact integer fraction tuples with 1<=num<den<=100')
        params.append(Fraction(*pair))
    w,a,b=params;responsibilities=[]
    for x in observations:
        left=w*(a if x else 1-a);right=(1-w)*(b if x else 1-b)
        responsibilities.append(left/(left+right))
    mass=sum(responsibilities);other=len(observations)-mass
    new_weight=mass/len(observations)
    new_a=sum(r*x for r,x in zip(responsibilities,observations))/mass
    new_b=sum((1-r)*x for r,x in zip(responsibilities,observations))/other
    pair=lambda x:(x.numerator,x.denominator)
    return {'responsibilities':[pair(r) for r in responsibilities],'weight':pair(new_weight),'p1':pair(new_a),'p2':pair(new_b),
            'claim':'PARTIAL','convergence_validated':False}
