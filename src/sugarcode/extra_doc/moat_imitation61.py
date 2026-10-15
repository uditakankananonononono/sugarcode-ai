"""Row61 Moat Analysis - Assesses defensibility of competitive advantages.
PARTIAL: minimum supplied technology-acquisition cost to imitate all capabilities.
Exact dict costs, provides, required, prerequisites. Costs exact list1..8 ints1..8.
Provides exact technology-count list of exact nonempty lists of unique integer
capability indices0..5. Required exact nonempty list1..6 unique ints0..5.
Prerequisites exact list0..28 unique [u,v] pairs0<=u<v<technology_count: choosing
technology v requires u. Enumerate prerequisite-closed sets, cover every required
capability, minimize cost then count then lex indices. Return technologies/cost
or both None if impossible, claims3False. No empirical competitive defensibility.
NOT_CLAIMED: real moat, verified imitation costs, production readiness.
"""
from itertools import combinations
SCOPE='PARTIAL: exact supplied prerequisite-closed minimum imitation capability cover only'
NOT_CLAIMED=('real moat','verified imitation costs','production readiness')


def assess(data):
    if type(data) is not dict or set(data)!={'costs','provides','required','prerequisites'}:
        raise ValueError('exact dict with costs, provides, required, prerequisites required')
    costs=data['costs'];provides=data['provides'];required=data['required'];prerequisites=data['prerequisites']
    if type(costs) is not list or not 1<=len(costs)<=8:
        raise ValueError('costs must be an exact list of 1..8 items')
    for v in costs:
        if type(v) is not int or not 1<=v<=8:
            raise ValueError('costs must be exact integers 1..8')
    if type(provides) is not list or len(provides)!=len(costs):
        raise ValueError('provides must be an exact technology-count list')
    for row in provides+[required]:
        if type(row) is not list or not 1<=len(row)<=6:
            raise ValueError('capabilities must be exact lists of 1..6 items')
        for v in row:
            if type(v) is not int or not 0<=v<=5:
                raise ValueError('capabilities must be exact integers 0..5')
        if len(set(row))!=len(row):raise ValueError('capabilities must be unique per list')
    n=len(costs)
    if type(prerequisites) is not list or len(prerequisites)>28:
        raise ValueError('prerequisites must be an exact list of at most 28 pairs')
    seen=set()
    for edge in prerequisites:
        if type(edge) is not list or len(edge)!=2:
            raise ValueError('prerequisite must be an exact two-item list')
        if any(type(v) is not int or not 0<=v<n for v in edge):
            raise ValueError('prerequisite indices must be exact valid indices')
        u,v=edge
        if u>=v:raise ValueError('prerequisites must follow strict index order')
        if (u,v) in seen:raise ValueError('prerequisites must be unique')
        seen.add((u,v))
    candidates=[]
    for size in range(n+1):
        for subset in combinations(range(n),size):
            chosen=set(subset)
            if any(v in chosen and u not in chosen for u,v in prerequisites):continue
            covered={cap for i in subset for cap in provides[i]}
            if set(required)<=covered:candidates.append((sum(costs[i] for i in subset),size,subset))
    cost,_,subset=min(candidates) if candidates else (None,None,None)
    return {'technologies':list(subset) if subset is not None else None,'cost':cost,'claims':[False,False,False]}
