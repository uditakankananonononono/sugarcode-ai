"""Evolutionary Computation (canonical1999): PARTIAL caller Moran birth-death chain.

population exactint2..8,mutants exactint0..population,fitness exactint1..4.
Onebirthproportionaltofitness(mutantfitness,other1),onedeathuniformindependent;
0,Nabsorbing. Returnmutantfixationprobabilityandexpectedstepsuntilabsorption.
Exactrationalbirthdeathdifferenceequations;no realbiologicalprediction.
Validationpopulation,mutants,fitness.Numericinputs only.
"""
from fractions import Fraction as F
SCOPE='PARTIAL: caller finite Moran chain fixation and absorption expectations'
NOT_CLAIMED=('real biological fitness','evolution prediction','measured population')


def fixation(population,mutants,fitness):
    for name,v,lo,hi in (('population',population,2,8),('mutants',mutants,0,population if type(population) is int else 0),('fitness',fitness,1,4)):
        if type(v) is not int or not lo<=v<=hi:raise ValueError(name+' exact int'+str(lo)+'..'+str(hi))
    n=population;lower=[];diagonal=[];upper=[];rhs=[]
    for i in range(1,n):
        up=F(fitness*i*(n-i),n*(fitness*i+n-i));down=F(i*(n-i),n*(fitness*i+n-i))
        lower.append(-down);diagonal.append(up+down);upper.append(-up);rhs.append([up if i==n-1 else F(0),F(1)])
    for i in range(1,n-1):
        factor=lower[i]/diagonal[i-1];diagonal[i]-=factor*upper[i-1];rhs[i]=[rhs[i][j]-factor*rhs[i-1][j] for j in range(2)]
    solutions=[[F(0),F(0)] for i in range(n-1)]
    for i in range(n-2,-1,-1):solutions[i]=[(rhs[i][j]-(upper[i]*solutions[i+1][j] if i<n-2 else 0))/diagonal[i] for j in range(2)]
    p,t=([F(0),F(0)] if mutants==0 else [F(1),F(0)] if mutants==n else solutions[mutants-1])
    return {'fixation_probability':p,'expected_absorption_steps':t,'evolution_validated':False}
