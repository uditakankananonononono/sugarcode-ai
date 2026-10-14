"""Row 325 Urban Planning: exact finite community facility selection.

Selects a fixed count of candidate facilities minimizing supplied resident
weights times Manhattan distance to the nearest selected facility. Generates
a finite community service configuration with resident assignments.
NOT_CLAIMED: social equity validation, traffic simulation, zoning compliance,
geographic road distance, political feasibility or physical deployment.
"""
from itertools import combinations


def select_facilities(residents,weights,candidates,facility_count):
    if any(type(v) not in (list,tuple) for v in (residents,weights,candidates)):
        raise TypeError('inputs must be lists or tuples')
    m=len(residents);n=len(candidates)
    if not 1<=m<=32:raise ValueError('resident count must be between 1 and 32')
    if not 1<=n<=12:raise ValueError('candidate count must be between 1 and 12')
    if len(weights)!=m:raise ValueError('weights must match residents')
    if type(facility_count) is not int or not 1<=facility_count<=n:
        raise ValueError('facility_count must be a nonbool integer inside candidate range')
    for point in list(residents)+list(candidates):
        if type(point) not in (list,tuple) or len(point)!=2:raise ValueError('points must have two coordinates')
        if any(type(v) is not int or not -1000<=v<=1000 for v in point):
            raise ValueError('coordinates must be nonbool integers between -1000 and 1000')
    if any(type(w) is not int or not 0<=w<=1000000 for w in weights):
        raise ValueError('weights must be nonbool integers zero through 1000000')
    distances=[[abs(a-x)+abs(b-y) for x,y in candidates] for a,b in residents]
    best=None;evaluated=0
    for chosen in combinations(range(n),facility_count):
        evaluated+=1
        assigned=[min(chosen,key=row.__getitem__) for row in distances]
        ds=[row[j] for row,j in zip(distances,assigned)]
        cost=sum(w*d for w,d in zip(weights,ds))
        if best is None or cost<best[0]:best=(cost,chosen,assigned,ds)
    cost,chosen,assigned,ds=best
    return {'facility_indices':list(chosen),'resident_assignments':assigned,
            'resident_distances':ds,'weighted_distance':cost,'evaluated_subsets':evaluated,'equity_validated':False}
