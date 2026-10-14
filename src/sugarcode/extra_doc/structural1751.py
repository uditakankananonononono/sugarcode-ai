"""Doc row1751 Structuralism: PARTIAL supplied directed relation degree ledger.

Nodes exact list1..100 unique nonblank exact str1..80. Edges exact list0..100
unique tuples(source,target), endpoints same labels and known nodes. Loops allowed.
Return indegrees/outdegrees in node order and reciprocated nonloop pairs sorted.
No inferred cultural structure, structuralist interpretation or validity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_relations(nodes,edges):
    if type(nodes) is not list or not 1<=len(nodes)<=100 or any(not _label(x) for x in nodes) or len(set(nodes))!=len(nodes):raise ValueError('nodes must be an exact list of 1..100 unique valid labels')
    if type(edges) is not list or len(edges)>100:raise ValueError('edges must be an exact list with 0..100 entries')
    seen=set()
    for edge in edges:
        if type(edge) is not tuple or len(edge)!=2:raise ValueError('edge must be a source target tuple')
        a,b=edge
        if not _label(a) or not _label(b) or a not in nodes or b not in nodes:raise ValueError('endpoints must be known valid labels')
        if edge in seen:raise ValueError('edges must be unique')
        seen.add(edge)
    degrees=[(n,sum(b==n for a,b in edges),sum(a==n for a,b in edges)) for n in nodes]
    reciprocal=sorted((a,b) for a,b in edges if a<b and (b,a) in seen)
    return {'degrees':degrees,'reciprocal_pairs':reciprocal,'claim':'PARTIAL','structure_validated':False}
