"""Doc row679 Hexagonal Architecture: PARTIAL supplied port-binding audit.

ports exact list0..50 unique nonblank exact str<=80; bindings exact list0..100
(port,adapter) exact tuples of valid labels. Report unbound declared ports,
undeclared binding indexes, multi-bound declared ports, repeated binding indexes
(after first occurrence). No code dependency inspection or runtime wiring claim.
"""


def _valid(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit(ports,bindings):
    if type(ports) is not list or len(ports)>50:
        raise ValueError('ports must be an exact list with 0..50 entries')
    if any(not _valid(x) for x in ports) or len(set(ports))!=len(ports):
        raise ValueError('ports must be unique valid labels')
    if type(bindings) is not list or len(bindings)>100:
        raise ValueError('bindings must be an exact list with 0..100 entries')
    if any(type(r) is not tuple or len(r)!=2 or any(not _valid(x) for x in r) for r in bindings):
        raise ValueError('bindings must be valid port adapter tuples')
    assigned={p:set() for p in ports};seen=set();duplicates=[];unknown=[]
    for i,(p,a) in enumerate(bindings):
        if (p,a) in seen:duplicates.append(i)
        seen.add((p,a))
        if p not in assigned:unknown.append(i)
        else:assigned[p].add(a)
    return {'unbound':[p for p in ports if not assigned[p]],
            'unknown':unknown,'multiple':[(p,sorted(assigned[p])) for p in ports if len(assigned[p])>1],
            'duplicates':duplicates,'claim':'PARTIAL','wiring_validated':False}
