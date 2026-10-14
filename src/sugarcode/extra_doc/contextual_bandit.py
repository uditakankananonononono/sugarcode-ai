"""Row253 Contextual Bandits: exact bounded disjoint ridge LinUCB transition.

SCOPED supplied integer contexts/rewards and observed arm feedback. Exact
Fraction weights, means and squared exploration bonuses; radical score order
is compared algebraically without float approximations. Lowest arm wins ties.
NOT_CLAIMED: online environment interaction, regret guarantee, randomized
policy, propensity correction, nonstationary/context-distribution modeling,
feedback validity or full production bandit service. Module PARTIAL.
"""
from fractions import Fraction as F


def _integer(x,low,high):
    if type(x) is not int:
        raise TypeError('exact nonbool integer required')
    if not low<=x<=high:
        raise ValueError('integer budget exceeded')
    return x


def _solve(A,b):
    n=len(b)
    a=[row[:]+[value] for row,value in zip(A,b)]
    for i in range(n):
        pivot=a[i][i]
        a[i]=[x/pivot for x in a[i]]
        for j in range(n):
            if j!=i:
                factor=a[j][i]
                a[j]=[x-factor*y for x,y in zip(a[j],a[i])]
    return [row[-1] for row in a]


def _compare(m,a,n,b):
    """Compare m+sqrt(a) with n+sqrt(b), nonnegative rational a,b."""
    d=m-n
    if d<0:
        return -_compare(n,b,m,a)
    if a>=b:
        return 0 if d==0 and a==b else 1
    t=b-a-d*d
    if t<0:
        return 1
    q=t*t-4*d*d*a
    return -1 if q>0 else 1 if q<0 else 0


def contextual_bandit(arms,feedback,context,*,ridge=1,alpha=1):
    _integer(arms,1,4)
    _integer(ridge,1,100)
    _integer(alpha,0,10)
    if not isinstance(context,list) or not 1<=len(context)<=2:
        raise ValueError('context budget 1..2 required')
    if not isinstance(feedback,list) or len(feedback)>100:
        raise ValueError('feedback budget 0..100 required')
    d=len(context)
    for x in context:_integer(x,-1000,1000)
    # Validate every row before building any sufficient statistics.
    for row in feedback:
        if not isinstance(row,(tuple,list)) or len(row)!=3:
            raise ValueError('feedback row requires arm/context/reward')
        arm,x,y=row
        _integer(arm,0,arms-1)
        if not isinstance(x,list) or len(x)!=d:
            raise ValueError('feedback context dimension mismatch')
        for v in x:_integer(v,-1000,1000)
        _integer(y,-1000,1000)
    matrices=[[[F(ridge if i==j else 0) for j in range(d)] for i in range(d)] for _ in range(arms)]
    vectors=[[F(0) for _ in range(d)] for _ in range(arms)]
    counts=[0]*arms
    for arm,x,y in feedback:
        counts[arm]+=1
        for i in range(d):
            vectors[arm][i]+=x[i]*y
            for j in range(d):matrices[arm][i][j]+=x[i]*x[j]
    weights=[];means=[];bonuses=[]
    for A,b in zip(matrices,vectors):
        w=_solve(A,b);z=_solve(A,[F(x) for x in context])
        weights.append(w)
        means.append(sum(x*y for x,y in zip(context,w)))
        bonuses.append(alpha*alpha*sum(x*y for x,y in zip(context,z)))
    chosen=0
    for arm in range(1,arms):
        if _compare(means[arm],bonuses[arm],means[chosen],bonuses[chosen])>0:chosen=arm
    return {'weights':weights,'means':means,'bonus_squared':bonuses,
            'counts':counts,'chosen_arm':chosen}
