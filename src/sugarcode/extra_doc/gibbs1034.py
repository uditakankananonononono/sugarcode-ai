"""Doc row1034 Gibbs Sampling: PARTIAL deterministic conditional sweep fixture.

weights exact list2 exact lists2 of exact nonbool ints1..100, joint masses for
binary(x,y). State exact tuple2 of exact ints0/1; draws exact tuple2 of exact
fractions(num,den), ints0<=num<den<=100. Update x given old y then y given new x,
choose1 iff draw strictly below conditional probability1. Return state and
conditional probabilities. No random generation, convergence or inference claim.
"""
from fractions import Fraction


def sweep(weights,state,draws):
    if type(weights) is not list or len(weights)!=2 or any(type(r) is not list or len(r)!=2 for r in weights):
        raise ValueError('weights must be an exact two by two list')
    if any(type(x) is not int or not 1<=x<=100 for r in weights for x in r):
        raise ValueError('weights must be integers in 1..100')
    if type(state) is not tuple or len(state)!=2 or any(type(x) is not int or x not in (0,1) for x in state):
        raise ValueError('state must be an exact tuple of binary integers')
    if type(draws) is not tuple or len(draws)!=2:
        raise ValueError('draws must be an exact tuple of two fractions')
    fractions=[]
    for pair in draws:
        if type(pair) is not tuple or len(pair)!=2 or any(type(x) is not int for x in pair) or not 0<=pair[0]<pair[1]<=100:
            raise ValueError('draws must be exact integer fractions with 0<=num<den<=100')
        fractions.append(Fraction(*pair))
    y=state[1];px=Fraction(weights[1][y],weights[0][y]+weights[1][y]);x=int(fractions[0]<px)
    py=Fraction(weights[x][1],weights[x][0]+weights[x][1]);y=int(fractions[1]<py)
    pair=lambda p:(p.numerator,p.denominator)
    return {'state':(x,y),'conditionals':(pair(px),pair(py)),'claim':'PARTIAL','convergence_validated':False}
