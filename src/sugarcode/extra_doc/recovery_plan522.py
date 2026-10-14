"""Row522 Disaster Recovery - Plans for catastrophes.
Exact single-crew prerequisite restoration schedule minimizing weighted service
completion time. Services are (restore duration, criticality weight) tuples.
Enumerate feasible orders; ties lexicographic service indices. Report completion
ledger, modeled total disruption and makespan. 1..8 services/durations1..10**6/
weights1..1000, at most8 prerequisites each. No running restore operation.
NOT_CLAIMED: catastrophe prediction, valid duration estimates, full continuity
plan, resilience certification, live restoration, external actions or recovery SLA.
"""
from itertools import permutations


def plan(services, prerequisites):
    if type(services) is not list or not 1<=len(services)<=8:raise ValueError('1..8 services before scan')
    n=len(services)
    if type(prerequisites) is not list or len(prerequisites)!=n:raise ValueError('matching prerequisite lists')
    for ds in prerequisites:
        if type(ds) is not list or len(ds)>8:raise ValueError('at most8 prerequisites before scan')
    for s in services:
        if type(s) is not tuple or len(s)!=2:raise ValueError('service duration weight pair')
        d,w=s
        if type(d) is not int or not 1<=d<=10**6:raise ValueError('duration integer1..1000000')
        if type(w) is not int or not 1<=w<=1000:raise ValueError('weight integer1..1000')
    for i,ds in enumerate(prerequisites):
        if any(type(j) is not int or not 0<=j<n or j==i for j in ds):raise ValueError('valid nonself prerequisite indices')
        if len(set(ds))!=len(ds):raise ValueError('unique prerequisites')
    best=None
    for order in permutations(range(n)):
        pos={s:i for i,s in enumerate(order)}
        if any(pos[j]>pos[i] for i,ds in enumerate(prerequisites) for j in ds):continue
        elapsed=0;cost=0;trace=[]
        for i in order:
            d,w=services[i];start=elapsed;elapsed+=d;cost+=elapsed*w
            trace.append({'service':i,'start':start,'complete':elapsed,'weighted_disruption':elapsed*w})
        key=(cost,order)
        if best is None or key<best[0]:best=(key,trace,elapsed)
    if best is None:raise ValueError('prerequisites must be acyclic')
    return {'order':best[0][1],'weighted_disruption':best[0][0],'timeline':best[1],'makespan':best[2],'restoration_performed':False}
