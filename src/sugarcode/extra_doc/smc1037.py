"""Doc row1037 Sequential Monte Carlo: PARTIAL exact importance-weight update.

prior/likelihood exact lists same length1..50, entries nonbool ints0..100.
Products must have positive sum. Return normalized rational weights and exact
ESS=1/sum(w²). No particles generated, resampling, filtering model or convergence.
"""
from fractions import Fraction


def update(prior,likelihood):
    if type(prior) is not list or not 1<=len(prior)<=50:
        raise ValueError('prior must be an exact list with 1..50 entries')
    if type(likelihood) is not list or len(likelihood)!=len(prior):
        raise ValueError('likelihood must be an exact list matching prior count')
    if any(type(x) is not int or not 0<=x<=100 for row in (prior,likelihood) for x in row):
        raise ValueError('weights must be integers in 0..100')
    products=[a*b for a,b in zip(prior,likelihood)];total=sum(products)
    if total==0:raise ValueError('updated weight sum must be positive')
    weights=[Fraction(x,total) for x in products];ess=1/sum(w*w for w in weights)
    pair=lambda x:(x.numerator,x.denominator)
    return {'weights':[pair(w) for w in weights],'ess':pair(ess),'claim':'PARTIAL','filter_validated':False}
