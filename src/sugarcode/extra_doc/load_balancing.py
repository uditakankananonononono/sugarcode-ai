"""Row519 Load Balancing: exact online least-projected normalized load dispatch.

For each supplied request weight, choose available server minimizing
(currentload+request)/capacity, ties lower serverindex; update load. Unavailable
servers excluded; reject if none. Caps16servers/64requests/32bitweightsloads,
capacity1..1000. NOT_CLAIMED: live traffic routing, server health validation,
global optimum, queue delays, network deployment or real capacity.
"""
from fractions import Fraction


def dispatch_requests(loads,capacities,available,requests):
    if any(type(v) not in (list,tuple) for v in (loads,capacities,available,requests)):raise TypeError('inputs must be lists or tuples')
    n=len(loads)
    if not 1<=n<=16 or len(requests)>64:raise ValueError('server count must be 1..16 and at most 64 requests allowed')
    if len(capacities)!=n or len(available)!=n:raise ValueError('server shapes must agree')
    if any(type(v) is not int or not 0<=v<=2**32-1 for v in [*loads,*requests]):raise ValueError('loads and requests must be nonbool integers zero through 4294967295')
    if any(type(v) is not int or not 1<=v<=1000 for v in capacities):raise ValueError('capacities must be nonbool integers one through 1000')
    if any(type(v) is not bool for v in available):raise TypeError('availability flags must be bool')
    active=[i for i,v in enumerate(available) if v]
    if not active:raise ValueError('at least one server must be available')
    result=list(loads);assignments=[]
    for weight in requests:
        i=min(active,key=lambda i:(Fraction(result[i]+weight,capacities[i]),i));result[i]+=weight;assignments.append(i)
    return {'server_indices':assignments,'final_loads':result,'normalized_loads':[Fraction(v,c) for v,c in zip(result,capacities)],'traffic_routed':False}
