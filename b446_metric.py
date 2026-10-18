"""Bounded exact finite metric-space arithmetic over supplied distances.

SCOPE: square matrices of nonnegative integer distances<=100, size1..6.
NOT_CLAIMED: distance inference, phylogenetics, shortest paths, integration.
"""
from fractions import Fraction
from itertools import combinations,product
CLAIMS=False
SCOPE="bounded exact finite metric-space invariants"
NOT_CLAIMED="distance inference, phylogenetics, shortest paths, product integration"
MAX_POINTS=6
MAX_DISTANCE=100


def _matrix(matrix):
    if type(matrix) not in (list, tuple):raise TypeError("matrix must be a list or tuple")
    n=len(matrix)
    if not 1<=n<=MAX_POINTS:raise ValueError("point count out of range")
    for row in matrix:
        if type(row) not in (list, tuple):raise TypeError("row must be a list or tuple")
        if len(row)!=n:raise ValueError("matrix must be square")
    for row in matrix:
        for x in row:
            if type(x) is not int:raise TypeError("distance must be an integer")
            if x<0 or x>MAX_DISTANCE:raise ValueError("distance out of range")
    return tuple(tuple(row) for row in matrix)


def _defects(a):
    n=len(a)
    return (sum(a[i][i]!=0 for i in range(n))+
            sum(a[i][j]==0 or a[i][j]!=a[j][i] for i in range(n) for j in range(i+1,n))+
            sum(a[i][j]>a[i][k]+a[k][j] for i,j,k in product(range(n),repeat=3)))


def _metric(matrix):
    a=_matrix(matrix)
    if _defects(a):raise ValueError("matrix must be a metric")
    return a


def _radius(x):
    if type(x) is not int:raise TypeError("radius must be an integer")
    if x<0 or x>MAX_DISTANCE:raise ValueError("radius out of range")
    return x


def metric_defect_count(matrix):return _defects(_matrix(matrix))


def is_metric(matrix):return _defects(_matrix(matrix))==0


def diameter(matrix):
    a=_metric(matrix)
    return max(map(max,a))


def eccentricities(matrix):
    a=_metric(matrix)
    return tuple(map(max,a))


def radius(matrix):
    a=_metric(matrix)
    return min(map(max,a))


def centers(matrix):
    a=_metric(matrix);r=min(map(max,a))
    return tuple(i for i,row in enumerate(a) if max(row)==r)


def is_ultrametric(matrix):
    a=_metric(matrix);n=len(a)
    return all(a[i][j]<=max(a[i][k],a[k][j]) for i,j,k in product(range(n),repeat=3))


def four_point_hyperbolicity(matrix):
    a=_metric(matrix);n=len(a);delta=0
    for i,j,k,l in product(range(n),repeat=4):
        sums=sorted((a[i][j]+a[k][l],a[i][k]+a[j][l],a[i][l]+a[j][k]))
        delta=max(delta,sums[2]-sums[1])
    return Fraction(delta,2)


def covering_number(matrix,ball_radius):
    """Minimum number of closed balls with centers in the supplied space."""
    a=_metric(matrix);r=_radius(ball_radius);n=len(a)
    for size in range(1,n+1):
        if any(all(any(a[x][center]<=r for center in selected) for x in range(n)) for selected in combinations(range(n),size)):return size
    raise AssertionError("unreachable covering")


def packing_number(matrix,separation):
    """Maximum subset whose distinct pairs have distance strictly > separation."""
    a=_metric(matrix);r=_radius(separation);n=len(a)
    for size in range(n,0,-1):
        if any(all(a[x][y]>r for x,y in combinations(selected,2)) for selected in combinations(range(n),size)):return size
    raise AssertionError("unreachable packing")
