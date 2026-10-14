"""Row 358 Transition Design: finite prerequisite-closed change portfolio.

Selects supplied change actions under a budget, requiring every selected
prerequisite also selected. Maximizes supplied benefits, then minimizes cost,
then selected index tuple. Returns a dependency-valid execution order.
Caps 12 actions/12 prerequisites each, 4096 portfolios.
NOT_CLAIMED: actual systemic change, causal benefit validation, organizational
consent, stakeholder consultation, policy success or deployment.
"""


def transition_portfolio(costs,benefits,prerequisites,budget):
    if any(type(v) not in (list,tuple) for v in (costs,benefits,prerequisites)):
        raise TypeError('inputs must be lists or tuples')
    n=len(costs)
    if not 1<=n<=12:raise ValueError('action count must be between 1 and 12')
    if len(benefits)!=n or len(prerequisites)!=n:raise ValueError('action shapes must agree')
    if type(budget) is not int or not 0<=budget<=1000000:raise ValueError('budget must be a nonbool integer zero through 1000000')
    for deps in prerequisites:
        if type(deps) not in (list,tuple) or len(deps)>12:raise ValueError('prerequisites must be lists or tuples of at most 12')
    if any(type(v) is not int or not 0<=v<=1000000 for v in list(costs)+list(benefits)):
        raise ValueError('costs and benefits must be nonbool integers zero through 1000000')
    for i,deps in enumerate(prerequisites):
        if any(type(j) is not int or not 0<=j<n or j==i for j in deps):raise ValueError('prerequisite indices must be nonbool valid nonself indices')
        if len(set(deps))!=len(deps):raise ValueError('prerequisites must be unique')
    pending=set(range(n));order=[]
    while pending:
        ready=[i for i in sorted(pending) if all(j not in pending for j in prerequisites[i])]
        if not ready:raise ValueError('prerequisite graph must be acyclic')
        i=ready[0];order.append(i);pending.remove(i)
    best=None;feasible=0
    for mask in range(1<<n):
        chosen=tuple(i for i in range(n) if mask&(1<<i));chosen_set=set(chosen)
        if any(j not in chosen_set for i in chosen for j in prerequisites[i]):continue
        cost=sum(costs[i] for i in chosen)
        if cost>budget:continue
        feasible+=1;benefit=sum(benefits[i] for i in chosen);key=(-benefit,cost,chosen)
        if best is None or key<best:best=key
    negative,cost,chosen=best
    return {'action_indices':list(chosen),'execution_order':[i for i in order if i in chosen],
            'cost':cost,'benefit':-negative,'feasible_count':feasible,'systemic_change_validated':False}
