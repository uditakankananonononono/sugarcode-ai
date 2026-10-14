"""Row255 Upper Confidence Bound: exact supplied-log UCB score transition.

SCOPED bounded observed rational rewards, counts/means and exact optimistic
ordering mean+sqrt(coefficient*log_value/count). Untried arms precede tried
arms, lowest index ties. log_value is a supplied approximation to ln(total);
its correctness is NOT_CLAIMED. NOT_CLAIMED transcendental logarithm,
online action/reward execution, classical UCB1 regret guarantees, stochastic
reward provenance or complete literal bandit service. Module PARTIAL.
"""
from fractions import Fraction as F


def _integer(x,low,high):
    if type(x) is not int:raise TypeError('exact nonbool integer required')
    if not low<=x<=high:raise ValueError('integer budget exceeded')
    return x


def _rational(x,high):
    if type(x) not in (int,F):raise TypeError('rational nonbool value required')
    if type(x) is int:
        if abs(x)>high:raise ValueError('rational range exceeded')
    else:
        if abs(x.numerator)>10**100 or x.denominator>10**100:raise ValueError('rational size budget exceeded')
    if not 0<=x<=high:raise ValueError('rational range exceeded')
    return F(x)


def _compare(m,a,n,b):
    d=m-n
    if d<0:return -_compare(n,b,m,a)
    if a>=b:return 0 if d==0 and a==b else 1
    t=b-a-d*d
    if t<0:return 1
    q=t*t-4*d*d*a
    return -1 if q>0 else 1 if q<0 else 0


def upper_confidence_bound(arms,feedback,*,log_value,coefficient=2):
    _integer(arms,1,4);_integer(coefficient,0,10)
    log_value=_rational(log_value,100)
    if not isinstance(feedback,list) or len(feedback)>100:raise ValueError('feedback budget 0..100 required')
    for row in feedback:
        if type(row) is not tuple or len(row)!=2:raise ValueError('arm/reward pair required')
        _integer(row[0],0,arms-1);_rational(row[1],1)
    counts=[0]*arms;sums=[F(0)]*arms
    for arm,reward in feedback:counts[arm]+=1;sums[arm]+=reward
    means=[s/n if n else None for s,n in zip(sums,counts)]
    bonus=[coefficient*log_value/n if n else None for n in counts]
    chosen=next((i for i,n in enumerate(counts) if n==0),None)
    if chosen is None:
        chosen=0
        for i in range(1,arms):
            if _compare(means[i],bonus[i],means[chosen],bonus[chosen])>0:chosen=i
    return {'counts':counts,'means':means,'bonus_squared':bonus,'chosen_arm':chosen}
