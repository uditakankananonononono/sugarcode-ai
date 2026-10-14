"""Cuckoo Search - Brood parasitism-inspired.

PARTIAL: exact-rational one-generation candidate replacement and worst-nest
abandonment for sphere minimization. Caller-supplied flight/discovery proposals;
no claim of sampled Levy flights, converged optimum or general optimization.
"""
from fractions import Fraction
from math import isfinite
SCOPE='one rational cuckoo replacement and abandonment generation on sphere'


def generation(nests,flights,targets,discoveries,abandon=1):
    """Sequentially insert each supplied flight into its target if strictly better.

    Then replace worst `abandon` nests with caller discoveries, even if worse.
    Score sum(x^2); worst ties choose larger index first. Flight targets may repeat,
    sequential order matters. Nests1..16,dimension1..4,coords[-100,100]. Flights1..32,
    matching built-in int targetindices; discoveries exactly abandon vectors.
    abandon built-in int0..nestcount. Exact list/tuple vectors and mixed rows.
    Fractions over decimal inputs; no hidden RNG or Levy-distribution claim.
    """
    if type(nests) not in (list,tuple) or not 1<=len(nests)<=16:raise ValueError('nests must contain1..16 vectors')
    if type(abandon) is not int or not 0<=abandon<=len(nests):raise ValueError('abandon must be built-in int0..nestcount')
    if type(nests[0]) not in (list,tuple) or not 1<=len(nests[0])<=4:raise ValueError('vectors must have1..4 equal dimensions')
    dim=len(nests[0])
    def vector(row):
        if type(row) not in (list,tuple) or len(row)!=dim:raise ValueError('vectors must have1..4 equal dimensions')
        out=[]
        for x in row:
            if type(x) not in (int,float) or not -100<=x<=100 or not isfinite(x):raise ValueError('finite built-in cuckoo coordinate in[-100,100] required')
            out.append(Fraction(str(x)))
        return tuple(out)
    output=[vector(row) for row in nests]
    if type(flights) not in (list,tuple) or not 1<=len(flights)<=32 or type(targets) not in (list,tuple) or len(targets)!=len(flights):raise ValueError('flights1..32 and matching target sequence required')
    parsed=[vector(row) for row in flights]
    for target in targets:
        if type(target) is not int or not 0<=target<len(nests):raise ValueError('targets must be built-in int nest indices')
    if type(discoveries) not in (list,tuple) or len(discoveries)!=abandon:raise ValueError('exactly abandon discovery vectors required')
    new=[vector(row) for row in discoveries];score=lambda row:sum(x*x for x in row);accepted=[]
    for i,(row,target) in enumerate(zip(parsed,targets)):
        if score(row)<score(output[target]):output[target]=row;accepted.append((i,target))
    worst=tuple(sorted(range(len(output)),key=lambda i:(score(output[i]),i),reverse=True)[:abandon])
    for target,row in zip(worst,new):output[target]=row
    return {'nests':tuple(output),'scores':tuple(score(row) for row in output),'accepted':tuple(accepted),'abandoned':worst,'scope':SCOPE}
