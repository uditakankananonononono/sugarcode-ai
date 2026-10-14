"""Doc row681 Onion Architecture: PARTIAL supplied transitive dependency audit.

layers exact dict1..50 module IDs to nonbool integer0..10; labels nonblank exact
str<=80. edges exact list0..200 known-ID pair tuples. For each module, report
all reachable strictly outer-layer modules excluding itself, sorted; report
modules reachable from themselves through nonempty paths as cycles, sorted.
No parsing or correctness validation of actual code or architecture claimed.
"""


def audit(layers,edges):
    if type(layers) is not dict or not 1<=len(layers)<=50:
        raise ValueError('layers must be an exact dict with 1..50 entries')
    for name,layer in layers.items():
        if type(name) is not str or not 1<=len(name)<=80 or not name.strip():
            raise ValueError('IDs must be nonblank exact strings of 1..80 characters')
        if type(layer) is not int or not 0<=layer<=10:
            raise ValueError('layers must be integers in 0..10')
    if type(edges) is not list or len(edges)>200:
        raise ValueError('edges must be an exact list with 0..200 entries')
    for row in edges:
        if type(row) is not tuple or len(row)!=2 or any(type(x) is not str or x not in layers for x in row):
            raise ValueError('edges must be exact known ID pair tuples')
    adjacent={n:set() for n in layers}
    for a,b in edges:adjacent[a].add(b)
    violations=[];cyclic=[]
    for start in sorted(layers):
        seen=set();pending=list(adjacent[start])
        while pending:
            node=pending.pop()
            if node in seen:continue
            seen.add(node);pending.extend(adjacent[node]-seen)
        if start in seen:cyclic.append(start)
        outer=sorted(n for n in seen if n!=start and layers[n]>layers[start])
        if outer:violations.append((start,outer))
    return {'outward_reachability':violations,'cyclic_modules':cyclic,'claim':'PARTIAL','code_validated':False}
