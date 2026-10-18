"""Bounded exact finite-group arithmetic over caller-supplied Cayley tables.

SCOPE: operation tables of order 1..6, integer labels 0..n-1.
NOT_CLAIMED: group classification, symbolic presentations, retrieval, integration.
"""
CLAIMS=False
SCOPE="bounded caller-supplied Cayley table arithmetic"
NOT_CLAIMED="classification, symbolic presentations, retrieval, product integration"
MAX_ORDER=6


def _label(x,n):
    if isinstance(x,bool):raise TypeError("label must be an integer")
    if type(x) is not int:raise TypeError("label must be an integer")
    if x<0 or x>=n:raise ValueError("label out of range")
    return x


def _table(table):
    if type(table) not in (list,tuple):raise TypeError("table must be a list or tuple")
    n=len(table)
    if not 1<=n<=MAX_ORDER:raise ValueError("order out of range")
    for row in table:
        if type(row) not in (list,tuple):raise TypeError("row must be a list or tuple")
        if len(row)!=n:raise ValueError("table must be square")
    return tuple(tuple(_label(x,n) for x in row) for row in table)


def _identity(a):
    return next((e for e in range(len(a)) if all(a[e][x]==x and a[x][e]==x for x in range(len(a)))),None)


def _inverses(a,e):
    return tuple(next((y for y in range(len(a)) if a[x][y]==e and a[y][x]==e),None) for x in range(len(a)))


def _defects(a):
    n=len(a)
    return sum(a[a[x][y]][z]!=a[x][a[y][z]] for x in range(n) for y in range(n) for z in range(n))


def _group(table):
    a=_table(table);e=_identity(a)
    if e is None:raise ValueError("table must be a group")
    inv=_inverses(a,e)
    if any(x is None for x in inv) or _defects(a):raise ValueError("table must be a group")
    return a,e,inv


def _closure(a,e,seeds):
    result=set(seeds)|{e}
    while True:
        expanded=result|{a[x][y] for x in result for y in result}
        if expanded==result:return tuple(sorted(result))
        result=expanded


def associativity_defect_count(table):
    return _defects(_table(table))


def identity_element(table):
    return _identity(_table(table))


def inverse_elements(table):
    a=_table(table);e=_identity(a)
    if e is None:raise ValueError("table has no identity")
    return _inverses(a,e)


def is_group(table):
    a=_table(table);e=_identity(a)
    return e is not None and all(x is not None for x in _inverses(a,e)) and _defects(a)==0


def is_abelian_group(table):
    a,e,inv=_group(table)
    return all(a[x][y]==a[y][x] for x in range(len(a)) for y in range(len(a)))


def center_elements(table):
    a,e,inv=_group(table)
    return tuple(x for x in range(len(a)) if all(a[x][y]==a[y][x] for y in range(len(a))))


def conjugacy_classes(table):
    a,e,inv=_group(table);seen=set();out=[]
    for x in range(len(a)):
        if x not in seen:
            orbit=tuple(sorted({a[a[g][x]][inv[g]] for g in range(len(a))}))
            out.append(orbit);seen.update(orbit)
    return tuple(out)


def element_orders(table):
    a,e,inv=_group(table);out=[]
    for x in range(len(a)):
        power=e
        for order in range(1,len(a)+1):
            power=a[power][x]
            if power==e:
                out.append(order);break
    return tuple(out)


def subgroup_generated(table,generators):
    a,e,inv=_group(table)
    if type(generators) not in (list,tuple):raise TypeError("generators must be a list or tuple")
    if len(generators)>MAX_ORDER:raise ValueError("generator count out of range")
    seen=set()
    for x in generators:
        _label(x,len(a))
        if x in seen:raise ValueError("generators must be distinct")
        seen.add(x)
    return _closure(a,e,seen)


def commutator_subgroup(table):
    a,e,inv=_group(table)
    seeds={a[a[a[x][y]][inv[x]]][inv[y]] for x in range(len(a)) for y in range(len(a))}
    return _closure(a,e,seeds)
