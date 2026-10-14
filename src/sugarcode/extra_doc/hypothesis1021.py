"""Doc row1021 Hypothesis Testing: PARTIAL exact two-sided fair-binomial fixture.

Given successes exact nonbool int0..trials and trials exact int1..100, compute
P under supplied fair-coin null by summing masses no greater than observed mass.
Return exact rational numerator/denominator. Caller alpha exact tuple(num,den),
nonbool ints,1<=num<den<=10000; rejection iff p<=alpha. No experimental design,
independence verification, scientific conclusions or multiplicity adjustment.
"""
from math import comb
from fractions import Fraction


def test(successes,trials,alpha):
    if type(trials) is not int or not 1<=trials<=100:
        raise ValueError('trials must be an integer in 1..100')
    if type(successes) is not int or not 0<=successes<=trials:
        raise ValueError('successes must be an integer in 0..trials')
    if type(alpha) is not tuple or len(alpha)!=2 or any(type(x) is not int for x in alpha) or not 1<=alpha[0]<alpha[1]<=10000:
        raise ValueError('alpha must be an exact integer fraction tuple with 1<=num<den<=10000')
    threshold=comb(trials,successes)
    p=Fraction(sum(comb(trials,k) for k in range(trials+1) if comb(trials,k)<=threshold),2**trials)
    return {'p':(p.numerator,p.denominator),'reject':p<=Fraction(*alpha),
            'claim':'PARTIAL','assumptions_validated':False}
