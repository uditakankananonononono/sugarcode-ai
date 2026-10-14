"""Doc row1032 Markov Chain Monte Carlo: PARTIAL exact two-state chain fixture.

Input p01,p10 exact tuple(num,den), nonbool ints1<=num<den<=100, initial exact
int0/1 and steps exact int0..100. Return exact state1 mass after transitions and
stationary state1 mass p01/(p01+p10). No random sampling, mixing or inference
validity claimed. Deterministic probability propagation, not a full MCMC engine.
"""
from fractions import Fraction


def propagate(p01,p10,initial,steps):
    params=[]
    for pair in (p01,p10):
        if type(pair) is not tuple or len(pair)!=2 or any(type(x) is not int for x in pair) or not 1<=pair[0]<pair[1]<=100:
            raise ValueError('probabilities must be exact integer fractions with 1<=num<den<=100')
        params.append(Fraction(*pair))
    if type(initial) is not int or initial not in (0,1):
        raise ValueError('initial must be an exact integer zero or one')
    if type(steps) is not int or not 0<=steps<=100:
        raise ValueError('steps must be an integer in 0..100')
    a,b=params;mass=Fraction(initial)
    for _ in range(steps):mass=(1-mass)*a+mass*(1-b)
    stationary=a/(a+b);pair=lambda x:(x.numerator,x.denominator)
    return {'state1_mass':pair(mass),'stationary_state1':pair(stationary),
            'claim':'PARTIAL','mixing_validated':False}
