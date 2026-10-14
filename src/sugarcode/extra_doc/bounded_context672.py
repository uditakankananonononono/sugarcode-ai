"""Doc row672 Bounded Context: PARTIAL offline entity ownership boundary audit.

Owners is exact dict of0..100 entity IDs to context IDs; calls exact list of
0..500(entity,entity) tuples. IDs nonblank exact strings<=80. Every call endpoint
must exist. Reports same/cross-context input indexes and sorted context-to-context
edge counts. Does not infer correct domain boundaries or inspect actual code.
"""


def audit(owners, calls):
    if type(owners) is not dict or len(owners)>100:
        raise ValueError('owners must be an exact dict with 0..100 entries')
    if any(type(x) is not str or not 1<=len(x)<=80 or not x.strip() for pair in owners.items() for x in pair):
        raise ValueError('entity and context IDs must be nonblank strings of 1..80 characters')
    if type(calls) is not list or len(calls)>500:
        raise ValueError('calls must be an exact list with 0..500 entries')
    for call in calls:
        if type(call) is not tuple or len(call)!=2:
            raise ValueError('call must be an entity pair tuple')
        if any(type(x) is not str or x not in owners for x in call):
            raise ValueError('call endpoints must be exact known entity IDs')
    same,cross,counts=[],[],{}
    for i,(source,target) in enumerate(calls):
        a,b=owners[source],owners[target]
        if a==b:same.append(i)
        else:
            cross.append(i)
            counts[a,b]=counts.get((a,b),0)+1
    return {'same_context':same,'cross_context':cross,
            'context_edges':[(a,b,n) for (a,b),n in sorted(counts.items())],
            'claim':'PARTIAL','boundaries_validated':False}
