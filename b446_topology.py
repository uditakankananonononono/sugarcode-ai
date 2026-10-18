"""Bounded exact finite topology arithmetic on caller-supplied open masks.

SCOPE: 0..4 points, open subsets given as unique integer bitmasks.
NOT_CLAIMED: geometric topology, infinite spaces, inference, integration.
"""
CLAIMS=False
SCOPE="finite open-set mask arithmetic on at most four labelled points"
NOT_CLAIMED="geometric topology, infinite spaces, inference, product integration"
MAX_POINTS=4
MAX_OPENS=16


def _int(x,name,low,high):
    if type(x) is not int:raise TypeError(name+" must be an integer")
    if x<low or x>high:raise ValueError(name+" out of range")
    return x


def _family(n,opens):
    _int(n,'points',0,MAX_POINTS)
    if type(opens) not in (list, tuple):raise TypeError("opens must be a list or tuple")
    if len(opens)>MAX_OPENS:raise ValueError("open count out of range")
    out=set()
    for mask in opens:
        _int(mask,'mask',0,(1<<n)-1)
        if mask in out:raise ValueError("open masks must be distinct")
        out.add(mask)
    return out


def _valid(n,opens):
    return 0 in opens and (1<<n)-1 in opens and all(a|b in opens and a&b in opens for a in opens for b in opens)


def _topology(n,opens):
    data=_family(n,opens)
    if not _valid(n,data):raise ValueError("opens must form a topology")
    return data


def _subset(n,opens,mask):
    data=_topology(n,opens)
    _int(mask,'mask',0,(1<<n)-1)
    return data


def _interior(opens,mask):
    result=0
    for o in opens:
        if o&mask==o:result|=o
    return result


def _closure(n,opens,mask):
    full=(1<<n)-1
    return full^_interior(opens,full^mask)


def is_topology(n,opens):
    data=_family(n,opens)
    return _valid(n,data)


def interior(n,opens,mask):
    data=_subset(n,opens,mask)
    return _interior(data,mask)


def closure(n,opens,mask):
    data=_subset(n,opens,mask)
    return _closure(n,data,mask)


def boundary(n,opens,mask):
    data=_subset(n,opens,mask)
    return _closure(n,data,mask)&_closure(n,data,((1<<n)-1)^mask)


def derived_set(n,opens,mask):
    data=_subset(n,opens,mask)
    return sum(1<<x for x in range(n) if all(o&(mask&~(1<<x)) for o in data if o>>x&1))


def is_connected(n,opens):
    data=_topology(n,opens);full=(1<<n)-1
    return all(o in (0,full) or full^o not in data for o in data)


def is_t0(n,opens):
    data=_topology(n,opens)
    return all(any(bool(o>>x&1)!=bool(o>>y&1) for o in data) for x in range(n) for y in range(x+1,n))


def is_t1(n,opens):
    data=_topology(n,opens)
    return all(any(o>>x&1 and not o>>y&1 for o in data) for x in range(n) for y in range(n) if x!=y)


def is_hausdorff(n,opens):
    data=_topology(n,opens)
    return all(any(a>>x&1 and b>>y&1 and a&b==0 for a in data for b in data) for x in range(n) for y in range(x+1,n))


def specialization_relation(n,opens):
    """Pairs (x,y) such that x lies in closure({y})."""
    data=_topology(n,opens)
    return tuple((x,y) for x in range(n) for y in range(n) if all(not o>>x&1 or o>>y&1 for o in data))
