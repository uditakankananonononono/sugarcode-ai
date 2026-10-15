"""Row1176 Fertility Treatment Planning: PARTIAL finite-population transfer count law.
Supplied exact tuple(total,viable,draws), exact ints total1..30,viable0..30,
draws0..30 with viable<=total,draws<=total. Uniform draws without replacement;
return exact hypergeometric viable-count PMF, mean and probability at least one.
No independence approximation. Viability counts assumed known, not inferred;
no embryo selection, transfer recommendation or reproductive forecast.
NOT_CLAIMED: clinical viability, transfer advice, pregnancy prediction, production readiness.
"""
from fractions import Fraction as F
from math import comb
SCOPE='PARTIAL: exact supplied finite-population viable-draw distribution'
NOT_CLAIMED=('clinical viability','transfer advice','pregnancy prediction','production readiness')

def distribution(population):
    if type(population) is not tuple or len(population)!=3:raise ValueError('population must be exact tuple3')
    total,viable,draws=population
    for v,lo in [(total,1),(viable,0),(draws,0)]:
        if type(v) is not int or not lo<=v<=30:raise ValueError('bounded exact population counts required')
    if viable>total or draws>total:raise ValueError('counts exceed total')
    den=comb(total,draws);pmf=[]
    for k in range(draws+1):
        ways=comb(viable,k)*comb(total-viable,draws-k) if k<=viable and draws-k<=total-viable else 0
        pmf.append(F(ways,den))
    return {'pmf':pmf,'mean':F(draws*viable,total),'at_least_one':1-pmf[0],'clinical_validated':False}
