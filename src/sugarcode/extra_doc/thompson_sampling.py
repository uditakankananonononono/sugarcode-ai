"""Row254 Thompson Sampling: exact Beta-Bernoulli supplied-quantile step.

SCOPED observed successes/failures, integer Beta priors, caller-supplied rational
posterior quantiles. Exact polynomial CDF and dyadic inverse-CDF brackets.
Selection returned only when brackets prove dominance; unresolved overlap is
None. Caller quantiles must be independent uniform draws for actual Thompson
sampling; that provenance is NOT_CLAIMED. NOT_CLAIMED random generation,
continuous exact inverse, online effects, regret bounds, feedback validation
or literal complete bandit service. Module PARTIAL.
"""
from fractions import Fraction as F
from math import comb, factorial


def _integer(x,low,high):
    if type(x) is not int:raise TypeError('exact nonbool integer required')
    if not low<=x<=high:raise ValueError('integer budget exceeded')
    return x


def _cdf(a,b,x):
    # Integrate normalized x**(a-1) * (1-x)**(b-1) coefficient by coefficient.
    scale=F(factorial(a+b-1),factorial(a-1)*factorial(b-1))
    return scale*sum(F((-1)**k*comb(b-1,k),a+k)*x**(a+k) for k in range(b))


def thompson_sampling(feedback,quantiles,*,prior=(1,1),bits=8):
    _integer(bits,1,16)
    if not isinstance(feedback,list) or not 1<=len(feedback)<=4:raise ValueError('arm budget 1..4 required')
    if not isinstance(quantiles,list) or len(quantiles)!=len(feedback):raise ValueError('one quantile per arm required')
    if type(prior) is not tuple or len(prior)!=2:raise ValueError('two integer prior parameters required')
    for value in prior:_integer(value,1,10)
    for row in feedback:
        if type(row) is not tuple or len(row)!=2:raise ValueError('success/failure pair required')
        for value in row:_integer(value,0,20)
    for q in quantiles:
        if type(q) not in (int,F):raise TypeError('rational nonbool quantile required')
        if type(q) is int:
            _integer(q,0,1)
        else:
            if abs(q.numerator)>10**100 or q.denominator>10**100:raise ValueError('rational size budget exceeded')
            if not 0<=q<=1:raise ValueError('quantile range 0..1 required')
    posterior=[];brackets=[]
    for (s,f),q in zip(feedback,quantiles):
        a=prior[0]+s;b=prior[1]+f;posterior.append((a,b));lo=F(0);hi=F(1)
        if q==0:hi=lo
        elif q==1:lo=hi
        else:
            for _ in range(bits):
                mid=(lo+hi)/2;c=_cdf(a,b,mid)
                if c==q:lo=hi=mid;break
                if c<q:lo=mid
                else:hi=mid
        brackets.append((lo,hi))
    chosen=None
    for i,(lo,hi) in enumerate(brackets):
        if all(i==j or lo>other_hi or (lo==hi==other_lo==other_hi and i<j)
               for j,(other_lo,other_hi) in enumerate(brackets)):
            chosen=i;break
    return {'posterior':posterior,'draw_brackets':brackets,'chosen_arm':chosen}
