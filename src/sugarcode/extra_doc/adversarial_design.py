"""Row 357 Adversarial Design: exact finite productive-friction allocation.

Selects supplied review/checkpoint features maximizing explicitly supplied
error-prevention benefits under a total friction budget. At most 12 features;
no hidden persuasion or coercion. Ties prefer less friction, then index tuple.
NOT_CLAIMED: measured behavior change, coercive tactics, deception, subjective
productivity, actual user intervention or autonomous deployment.
"""


def productive_friction(friction,benefits,budget):
    if type(friction) not in (list,tuple) or type(benefits) not in (list,tuple):
        raise TypeError('friction and benefits must be lists or tuples')
    if not 1<=len(friction)<=12:raise ValueError('feature count must be between 1 and 12')
    if len(benefits)!=len(friction):raise ValueError('benefit count must match features')
    if type(budget) is not int or not 0<=budget<=1000000:
        raise ValueError('budget must be a nonbool integer zero through 1000000')
    if any(type(v) is not int or not 0<=v<=1000000 for v in list(friction)+list(benefits)):
        raise ValueError('friction and benefits must be nonbool integers zero through 1000000')
    best=None;feasible=0
    for mask in range(1<<len(friction)):
        chosen=tuple(i for i in range(len(friction)) if mask&(1<<i))
        cost=sum(friction[i] for i in chosen)
        if cost>budget:continue
        feasible+=1;benefit=sum(benefits[i] for i in chosen);key=(-benefit,cost,chosen)
        if best is None or key<best:best=key
    neg,cost,chosen=best
    return {'feature_indices':list(chosen),'friction':cost,'benefit':-neg,
            'feasible_count':feasible,'behavior_change_validated':False}
