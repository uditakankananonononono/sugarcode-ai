"""Row56 Ergodicity Awareness - Recognizes when time averages differ from ensemble averages.
PARTIAL: exact deterministic finite-state long-run reward time means. Exact dict
next,rewards,weights, equal exact lists1..7: next exact indices0..n-1, rewards
exact ints-5..5, weights exact ints0..5 with positive total. Each initial state
follows the deterministic map forever; discard transient prefix, average cycle
rewards. Return per-start time means, initial-weighted ensemble of time means,
between-start variance, same_mean flag over positive-weight starts, claims3False.
Not general stochastic ergodicity, pointwise ensemble convergence or inference.
NOT_CLAIMED: general ergodicity test, real process model, production readiness.
"""
from fractions import Fraction
SCOPE='PARTIAL: exact supplied deterministic finite-state cycle time-mean dispersion only'
NOT_CLAIMED=('general ergodicity test','real process model','production readiness')


def analyze(data):
    if type(data) is not dict or set(data)!={'next','rewards','weights'}:
        raise ValueError('exact dict with next, rewards, weights required')
    successor=data['next'];rewards=data['rewards'];weights=data['weights']
    if type(successor) is not list or not 1<=len(successor)<=7:
        raise ValueError('next must be an exact list of 1..7 items')
    n=len(successor)
    for v in successor:
        if type(v) is not int or not 0<=v<n:
            raise ValueError('next must contain exact valid state indices')
    for key,row in [('rewards',rewards),('weights',weights)]:
        if type(row) is not list or len(row)!=n:
            raise ValueError(key+' must be an exact state-length list')
        for v in row:
            if type(v) is not int or not (-5 if key=='rewards' else 0)<=v<=5:
                raise ValueError(key+' outside exact integer range')
    if not any(weights):raise ValueError('weights must have positive total')
    means=[]
    for start in range(n):
        seen={};path=[];state=start
        while state not in seen:
            seen[state]=len(path);path.append(state);state=successor[state]
        cycle=path[seen[state]:]
        means.append(Fraction(sum(rewards[i] for i in cycle),len(cycle)))
    total=sum(weights);ensemble=sum((w*v for w,v in zip(weights,means)),Fraction(0))/total
    variance=sum((w*(v-ensemble)**2 for w,v in zip(weights,means)),Fraction(0))/total
    def pair(v):return [v.numerator,v.denominator]
    return {'time_means':[pair(v) for v in means],'ensemble':pair(ensemble),'variance':pair(variance),'same_mean':variance==0,'claims':[False,False,False]}
