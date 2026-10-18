"""Bounded exact arithmetic on caller-supplied simple undirected graphs.

SCOPE: labelled vertices 0..n-1, n<=6, at most 15 unique edges, colors<=6.
NOT_CLAIMED: graph retrieval, large-graph performance, product integration.
"""
from fractions import Fraction
from itertools import combinations, product

CLAIMS = False
SCOPE = "exact invariants of small caller-supplied simple undirected graphs"
NOT_CLAIMED = "retrieval, large-graph performance, network, product integration"
MAX_VERTICES = 6
MAX_EDGES = 15
MAX_COLORS = 6


def _integer(x,name,low,high):
    if isinstance(x,bool):
        raise TypeError(name+" must be an integer")
    if not isinstance(x,int):
        raise TypeError(name+" must be an integer")
    if x<low or x>high:
        raise ValueError(name+" out of range")
    return x


def _graph(n,edges):
    _integer(n,'vertex count',0,MAX_VERTICES)
    if not isinstance(edges,(list,tuple)):
        raise TypeError("edges must be a list or tuple")
    if len(edges)>MAX_EDGES:
        raise ValueError("edge count out of range")
    out=[]
    seen=set()
    for edge in edges:
        if not isinstance(edge,(list,tuple)):
            raise TypeError("edge must be a list or tuple")
        if len(edge)!=2:
            raise ValueError("edge must have two endpoints")
        a=_integer(edge[0],'vertex',0,n-1)
        b=_integer(edge[1],'vertex',0,n-1)
        if a==b:
            raise ValueError("loops not allowed")
        pair=(min(a,b),max(a,b))
        if pair in seen:
            raise ValueError("edges must be distinct")
        seen.add(pair);out.append(pair)
    return n,tuple(out)


def _det(matrix):
    a=[[Fraction(x) for x in row] for row in matrix]
    result=Fraction(1)
    for i in range(len(a)):
        pivot=next((j for j in range(i,len(a)) if a[j][i]),None)
        if pivot is None:return 0
        if pivot!=i:
            a[i],a[pivot]=a[pivot],a[i];result=-result
        p=a[i][i];result*=p
        for j in range(i+1,len(a)):
            factor=a[j][i]/p
            for k in range(i+1,len(a)):a[j][k]-=factor*a[i][k]
    if result.denominator!=1:raise AssertionError("nonintegral determinant")
    return result.numerator


def _laplacian(n,edges):
    a=[[0]*n for _ in range(n)]
    for u,v in edges:
        a[u][u]+=1;a[v][v]+=1;a[u][v]-=1;a[v][u]-=1
    return a


def spanning_tree_count(n,edges):
    n,edges=_graph(n,edges)
    if n==0:return 0
    a=_laplacian(n,edges)
    return _det([row[:-1] for row in a[:-1]])


def rooted_forest_count(n,edges):
    n,edges=_graph(n,edges)
    a=_laplacian(n,edges)
    for i in range(n):a[i][i]+=1
    return _det(a)


def matching_count(n,edges):
    n,edges=_graph(n,edges)
    count=0
    for mask in range(1<<len(edges)):
        selected=[edge for i,edge in enumerate(edges) if mask>>i&1]
        endpoints=[x for edge in selected for x in edge]
        count+=len(endpoints)==len(set(endpoints))
    return count


def perfect_matching_count(n,edges):
    n,edges=_graph(n,edges)
    if n%2:return 0
    return sum(len({x for edge in selected for x in edge})==n for selected in combinations(edges,n//2))


def independent_set_count(n,edges):
    n,edges=_graph(n,edges)
    return sum(all(not(mask>>u&1 and mask>>v&1) for u,v in edges) for mask in range(1<<n))


def vertex_cover_count(n,edges):
    n,edges=_graph(n,edges)
    return sum(all(mask>>u&1 or mask>>v&1 for u,v in edges) for mask in range(1<<n))


def proper_coloring_count(n,edges,colors):
    n,edges=_graph(n,edges)
    _integer(colors,'colors',0,MAX_COLORS)
    return sum(all(assignment[u]!=assignment[v] for u,v in edges) for assignment in product(range(colors),repeat=n))


def chromatic_number(n,edges):
    n,edges=_graph(n,edges)
    for colors in range(n+1):
        if proper_coloring_count(n,edges,colors):return colors
    raise AssertionError("unreachable coloring")


def connected_component_count(n,edges):
    n,edges=_graph(n,edges)
    parent=list(range(n))
    def root(x):
        while parent[x]!=x:x=parent[x]
        return x
    for u,v in edges:parent[root(u)]=root(v)
    return len({root(x) for x in range(n)})


def cycle_rank(n,edges):
    n,edges=_graph(n,edges)
    return len(edges)-n+connected_component_count(n,edges)
