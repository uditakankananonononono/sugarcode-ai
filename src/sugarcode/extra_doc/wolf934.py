"""Wolf Pack Algorithm - Pack hunting-inspired.

PARTIAL: deterministic synchronous three-leader encircling generation on sphere
objective, a grey-wolf-style finite model. No actual wolves, trained policy,
general optimum guarantee or identity with every Wolf Pack Algorithm variant.
"""
from math import isfinite
SCOPE='three-leader synchronous encircling sphere generation; no optimum guarantee'


def encircle(points,coefficients,bound=10.0):
    """Choose three best old points by sphere score/index, move each point.

    3..16 agents,dim1..4,box[-bound,bound],bound(0,100]. coefficients one row per
    agent withthreeleader rows,each (A_vector,C_vector):A[-2,2],C[0,2].
    Newcoordinate mean overleaders(L-A*abs(C*L-oldX)),then clampbox. Supplied
    coefficients instead ofrandomdraws oriteration-schedule. Alloldstates used.
    Exactlist/tuple mixtures accepted atalllevels,built-in finite int/floatonly.
    Returns indicesoldleaders,newpositions/scores;leadersalso move. No hiddenRNG.
    """
    def real(x,lo,hi):
        if type(x) not in (int,float) or not lo<=x<=hi or not isfinite(x):raise ValueError('finite built-in wolf real outside range')
        return float(x)
    limit=real(bound,0,100)
    if limit==0:raise ValueError('bound must be positive')
    if type(points) not in (list,tuple) or not 3<=len(points)<=16:raise ValueError('points must contain3..16 vectors')
    if type(points[0]) not in (list,tuple) or not 1<=len(points[0])<=4:raise ValueError('vectors must have1..4 equal dimensions')
    dim=len(points[0])
    def vector(row,lo,hi):
        if type(row) not in (list,tuple) or len(row)!=dim:raise ValueError('vectors must have1..4 equal dimensions')
        return tuple(real(x,lo,hi) for x in row)
    p=[vector(row,-limit,limit) for row in points]
    if type(coefficients) not in (list,tuple) or len(coefficients)!=len(p):raise ValueError('one three-leader coefficient matrix per agent required')
    parsed=[]
    for row in coefficients:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('three leader coefficient pairs per agent required')
        pairs=[]
        for pair in row:
            if type(pair) not in (list,tuple) or len(pair)!=2:raise ValueError('each coefficient pair must contain A and C vectors')
            pairs.append((vector(pair[0],-2,2),vector(pair[1],0,2)))
        parsed.append(pairs)
    score=lambda row:sum(x*x for x in row)
    leaders=tuple(sorted(range(len(p)),key=lambda i:(score(p[i]),i))[:3]);output=[]
    for row,pairs in zip(p,parsed):
        new=[]
        for axis in range(dim):
            value=sum(p[index][axis]-a[axis]*abs(c[axis]*p[index][axis]-row[axis]) for index,(a,c) in zip(leaders,pairs))/3
            new.append(max(-limit,min(limit,value)))
        output.append(tuple(new))
    return {'leaders':leaders,'points':tuple(output),'scores':tuple(score(row) for row in output),'scope':SCOPE}
