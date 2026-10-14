"""Doc row1758 Actor-Network Theory: PARTIAL supplied heterogeneous graph reach.

Entities exact list2..20 tuples(id,kind), kind literal exact str human/nonhuman;
unique exact nonblank str IDs1..80. Links exact list0..100 unique directed tuples
(source,target), distinct known exact label endpoints. Return directed reachable
other entities per entity in input order. No inferred agency or theory validity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_network(entities,links):
    if type(entities) is not list or not 2<=len(entities)<=20:raise ValueError('entities must be an exact list with 2..20 entries')
    ids=set()
    for row in entities:
        if type(row) is not tuple or len(row)!=2:raise ValueError('entity must be an id kind tuple')
        name,kind=row
        if not _label(name) or name in ids:raise ValueError('entity IDs must be unique valid labels')
        ids.add(name)
        if type(kind) is not str or kind not in ('human','nonhuman'):raise ValueError('kind must be an exact human or nonhuman string')
    if type(links) is not list or len(links)>100:raise ValueError('links must be an exact list with 0..100 entries')
    seen=set()
    for edge in links:
        if type(edge) is not tuple or len(edge)!=2:raise ValueError('link must be a source target tuple')
        a,b=edge
        if not _label(a) or not _label(b) or a not in ids or b not in ids or a==b:raise ValueError('endpoints must be distinct known valid labels')
        if edge in seen:raise ValueError('links must be unique')
        seen.add(edge)
    reachable=[]
    for name,kind in entities:
        visited={name};pending=[name]
        while pending:
            current=pending.pop()
            for a,b in links:
                if a==current and b not in visited:visited.add(b);pending.append(b)
        reachable.append((name,sorted(visited-{name})))
    return {'reachable':reachable,'kinds':list(entities),'claim':'PARTIAL','agency_inferred':False,'theory_validated':False}
