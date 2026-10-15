"""Network Science (canonical2011): PARTIAL caller weighted spanning tree law.

weights exacttuple6 exactint0..3 forundirectededges01,02,03,12,13,23. Treeweight
productofedgeweights;partition=sumallspanningtreeweights. Returnpartitionand
edgeinclusionprobabilitiesunderweightproportionallaw(Noneforeachifpartition0).
Kirchhoffcofactor determinantandedgecontractionpartitioncomputeprobabilities.
No actualnetwork/physicalresistance/robustnessclaim. Validateouter/cells.
"""
from fractions import Fraction as F
SCOPE='PARTIAL: caller four-node weighted spanning-tree partition and edge inclusion law'
NOT_CLAIMED=('real network robustness','physical resistance','measured network')
EDGES=((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))


def _partition(n,edges):
    L=[[F(0)]*n for _ in range(n)]
    for a,b,w in edges:
        if a==b:continue
        L[a][a]+=w;L[b][b]+=w;L[a][b]-=w;L[b][a]-=w
    A=[row[:-1] for row in L[:-1]];result=F(1)
    for c in range(n-1):
        pivot=next((i for i in range(c,n-1) if A[i][c]),None)
        if pivot is None:return 0
        if pivot!=c:A[c],A[pivot]=A[pivot],A[c];result=-result
        v=A[c][c];result*=v
        for i in range(c+1,n-1):
            scale=A[i][c]/v
            for j in range(c,n-1):A[i][j]-=scale*A[c][j]
    return int(result)


def trees(weights):
    if type(weights) is not tuple or len(weights)!=6:raise ValueError('weights exact tuple6')
    for w in weights:
        if type(w) is not int or not 0<=w<=3:raise ValueError('weight exact int0..3')
    edges=[(a,b,w) for (a,b),w in zip(EDGES,weights)];Z=_partition(4,edges);probabilities=[]
    for index,(a,b,w) in enumerate(edges):
        groups=[i for i in range(4) if i!=b];mapping={i:groups.index(a if i==b else i) for i in range(4)};contracted=[(mapping[x],mapping[y],v) for x,y,v in edges]
        probabilities.append(F(w*_partition(3,contracted),Z) if Z else None)
    return {'partition':Z,'edge_probabilities':tuple(probabilities),'network_validated':False}
