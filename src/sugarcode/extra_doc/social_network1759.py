"""Doc row1759 Social Network Analysis: PARTIAL supplied undirected simple graph.

Nodes exact list2..20 unique exact nonblank str1..80. Edges exact list0..100
unique unordered pairs, exact tuples, distinct known endpoints. Return degrees
in supplied node order, components sorted and triangles sorted. No inferred social
relationships, influence, demographics or network validity.
"""
from itertools import combinations


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_graph(nodes,edges):
    if type(nodes) is not list or not 2<=len(nodes)<=20 or any(not _label(x) for x in nodes) or len(set(nodes))!=len(nodes):raise ValueError('nodes must be an exact list of 2..20 unique valid labels')
    if type(edges) is not list or len(edges)>100:raise ValueError('edges must be an exact list with 0..100 entries')
    seen=set();adj={n:set() for n in nodes}
    for edge in edges:
        if type(edge) is not tuple or len(edge)!=2:raise ValueError('edge must be a source target tuple')
        a,b=edge
        if not _label(a) or not _label(b) or a not in adj or b not in adj or a==b:raise ValueError('endpoints must be distinct known valid labels')
        pair=tuple(sorted(edge))
        if pair in seen:raise ValueError('undirected edges must be unique')
        seen.add(pair);adj[a].add(b);adj[b].add(a)
    remaining=set(nodes);components=[]
    while remaining:
        start=min(remaining);visited={start};pending=[start]
        while pending:
            current=pending.pop()
            for neighbor in adj[current]-visited:visited.add(neighbor);pending.append(neighbor)
        remaining-=visited;components.append(sorted(visited))
    triangles=[(a,b,c) for a,b,c in combinations(sorted(nodes),3) if b in adj[a] and c in adj[a] and c in adj[b]]
    return {'degrees':[(n,len(adj[n])) for n in nodes],'components':components,'triangles':triangles,'claim':'PARTIAL','social_inference':False}
