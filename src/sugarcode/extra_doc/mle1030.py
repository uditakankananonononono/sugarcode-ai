"""Doc row1030 Maximum Likelihood Estimation: PARTIAL Bernoulli grid fixture.

successes exact nonbool int0..trials, trials exact int1..100; grid exact list1..50
unique exact tuple(num,den) integer fractions0<=num<=den<=100, den>=1.
Duplicate normalized fractions invalid. Return maximizing supplied grid index,
probability and exact likelihood, earliest input on ties. Boundary0**0 is1.
No fitted model validity, continuous optimum or actual inference claim.
"""
from fractions import Fraction


def estimate(successes,trials,grid):
    if type(trials) is not int or not 1<=trials<=100:
        raise ValueError('trials must be an integer in 1..100')
    if type(successes) is not int or not 0<=successes<=trials:
        raise ValueError('successes must be an integer in 0..trials')
    if type(grid) is not list or not 1<=len(grid)<=50:
        raise ValueError('grid must be an exact list with 1..50 entries')
    probs=[]
    for pair in grid:
        if type(pair) is not tuple or len(pair)!=2 or any(type(x) is not int for x in pair) or not 0<=pair[0]<=pair[1]<=100 or pair[1]<1:
            raise ValueError('grid entries must be integer fraction tuples with 0<=num<=den<=100 and den>=1')
        value=Fraction(*pair)
        if value in probs:raise ValueError('grid probabilities must be distinct')
        probs.append(value)
    likelihoods=[p**successes*(1-p)**(trials-successes) for p in probs]
    index=max(range(len(probs)),key=lambda i:likelihoods[i]);p=probs[index];likelihood=likelihoods[index]
    return {'index':index,'probability':(p.numerator,p.denominator),'likelihood':(likelihood.numerator,likelihood.denominator),
            'claim':'PARTIAL','model_validated':False}
