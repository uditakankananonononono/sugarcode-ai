"""Row79 Signaling Theory - Interprets costly signals of quality.
PARTIAL: pure equilibria of supplied two-type costly-signal competitive-wage
model. Exact dict quality, prior, costs, offpath. Quality exact increasing pair
ints0..8; prior exact pair ints1..4. Costs exact two rows, common width1..4,
exact ints0..8. Offpath exact signal-width list ints0..4: high-type probability
numerator/4 for unused signals. For used signals infer high-type probability by
Bayes; wage=expected quality. Each type chooses signal maximizing wage-cost,
weak best responses allow ties. Return equilibria in lex strategy order, each
[strategy,belief pairs,wage pairs,utility pairs], claims3False. No real quality
inference or causal signaling claim. NOT_CLAIMED: actual quality inference,
real signaling equilibrium, production readiness.
"""
from fractions import Fraction
from itertools import product
SCOPE='PARTIAL: exact supplied two-type finite costly-signal wage equilibria only'
NOT_CLAIMED=('actual quality inference','real signaling equilibrium','production readiness')


def equilibria(data):
    if type(data) is not dict or set(data)!={'quality','prior','costs','offpath'}:
        raise ValueError('exact dict with quality, prior, costs, offpath required')
    quality=data['quality'];prior=data['prior'];costs=data['costs'];offpath=data['offpath']
    for key,row,lo,hi in [('quality',quality,0,8),('prior',prior,1,4)]:
        if type(row) is not list or len(row)!=2:
            raise ValueError(key+' must be an exact two-item list')
        for v in row:
            if type(v) is not int or not lo<=v<=hi:
                raise ValueError(key+' entries outside exact integer range')
    if quality[0]>=quality[1]:raise ValueError('quality must be strictly increasing')
    if type(costs) is not list or len(costs)!=2:
        raise ValueError('costs must be an exact two-row list')
    width=None
    for row in costs:
        if type(row) is not list or not 1<=len(row)<=4 or (width is not None and len(row)!=width):
            raise ValueError('cost rows must be exact equal-width lists of 1..4 items')
        width=len(row)
        for v in row:
            if type(v) is not int or not 0<=v<=8:
                raise ValueError('costs must be exact integers 0..8')
    if type(offpath) is not list or len(offpath)!=width:
        raise ValueError('offpath must be an exact signal-width list')
    for v in offpath:
        if type(v) is not int or not 0<=v<=4:
            raise ValueError('offpath must be exact integers 0..4')
    result=[]
    def pairs(row):return [[v.numerator,v.denominator] for v in row]
    for strategy in product(range(width),repeat=2):
        beliefs=[]
        for j in range(width):
            mass=sum(prior[t] for t in range(2) if strategy[t]==j)
            beliefs.append(Fraction(prior[1] if strategy[1]==j else 0,mass) if mass else Fraction(offpath[j],4))
        wages=[quality[0]*(1-p)+quality[1]*p for p in beliefs]
        utilities=[wages[strategy[t]]-costs[t][strategy[t]] for t in range(2)]
        if all(utilities[t]>=wages[j]-costs[t][j] for t in range(2) for j in range(width)):
            result.append([list(strategy),pairs(beliefs),pairs(wages),pairs(utilities)])
    return {'equilibria':result,'claims':[False,False,False]}
