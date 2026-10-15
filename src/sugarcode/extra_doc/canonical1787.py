"""Social Trust (canonical1787): PARTIAL caller signed graph structural balance.

adjacency exacttuple2..5 exacttupleN,exactint-1/0/1,symmetric,zerodiagonal.
+1 expects endpoints samebinarygroup,-1 different,0 noedge. Frustrationindex
fewest edges violatedbybinarypartition (equal to minimumedgedeletions to
balance). Return alloptimalbinaryassignments lexicographic,vertex0 fixed0,
violatededgepairs foreachassignment,balancedboolean. No realtrust inferred.
Validation outer,rows/cells,diagonal then symmetry row-major.
"""
from itertools import product
SCOPE='PARTIAL: caller signed-network frustration index and optimal balance partitions'
NOT_CLAIMED=('verified trust','relationship inference','social diagnosis')


def balance(adjacency):
    if type(adjacency) is not tuple or not 2<=len(adjacency)<=5:raise ValueError('adjacency exact tuple2..5')
    n=len(adjacency)
    for row in adjacency:
        if type(row) is not tuple or len(row)!=n:raise ValueError('row exact tupleN')
        for v in row:
            if type(v) is not int or v not in (-1,0,1):raise ValueError('edge exact int-1/0/1')
    for i in range(n):
        if adjacency[i][i]:raise ValueError('diagonal must be zero')
    for i in range(n):
        for j in range(n):
            if adjacency[i][j]!=adjacency[j][i]:raise ValueError('adjacency must be symmetric')
    best=None;partitions=[];violations=[]
    for tail in product((0,1),repeat=n-1):
        groups=(0,)+tail;bad=[(i,j) for i in range(n) for j in range(i+1,n) if adjacency[i][j] and (groups[i]==groups[j])!=(adjacency[i][j]==1)]
        if best is None or len(bad)<best:best=len(bad);partitions=[];violations=[]
        if len(bad)==best:partitions.append(groups);violations.append(bad)
    return {'frustration_index':best,'optimal_partitions':partitions,'violated_edges':violations,'balanced':best==0,'trust_validated':False}
