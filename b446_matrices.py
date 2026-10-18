"""Bounded exact square integer matrix arithmetic, dimensions 1..4.

SCOPE: caller-supplied square integer matrices, entries -100..100.
NOT_CLAIMED: floating conditioning, sparse scale, retrieval, integration.
"""
from fractions import Fraction
from itertools import permutations

CLAIMS = False
SCOPE = "exact bounded square integer matrix arithmetic"
NOT_CLAIMED = "floating conditioning, sparse scale, retrieval, product integration"
MAX_DIMENSION = 4
MAX_ENTRY = 100


def _entry(x):
    if type(x) is not int:raise TypeError("entry must be an integer")
    if abs(x)>MAX_ENTRY:raise ValueError("entry out of range")
    return x


def _matrix(matrix):
    if type(matrix) not in (list, tuple):raise TypeError("matrix must be a list or tuple")
    n=len(matrix)
    if not 1<=n<=MAX_DIMENSION:raise ValueError("dimension out of range")
    for row in matrix:
        if type(row) not in (list, tuple):raise TypeError("row must be a list or tuple")
        if len(row)!=n:raise ValueError("matrix must be square")
    return tuple(tuple(_entry(x) for x in row) for row in matrix)


def _reduce(a,columns):
    a=[[Fraction(x) for x in row] for row in a]
    pivot_row=0;pivots=[]
    for column in range(columns):
        index=next((i for i in range(pivot_row,len(a)) if a[i][column]),None)
        if index is None:continue
        a[index],a[pivot_row]=a[pivot_row],a[index]
        scale=a[pivot_row][column]
        a[pivot_row]=[x/scale for x in a[pivot_row]]
        for i in range(len(a)):
            if i!=pivot_row:
                factor=a[i][column]
                a[i]=[x-factor*y for x,y in zip(a[i],a[pivot_row])]
        pivots.append(column);pivot_row+=1
    return tuple(tuple(row) for row in a),tuple(pivots)


def _det(a):
    if not a:return 1
    total=0
    for j,value in enumerate(a[0]):
        minor=[row[:j]+row[j+1:] for row in a[1:]]
        total+=(-1)**j*value*_det(minor)
    return total


def determinant(matrix):
    return _det(_matrix(matrix))


def permanent(matrix):
    a=_matrix(matrix);n=len(a)
    total=0
    for order in permutations(range(n)):
        term=1
        for i,j in enumerate(order):term*=a[i][j]
        total+=term
    return total


def rank(matrix):
    a=_matrix(matrix)
    return len(_reduce(a,len(a))[1])


def nullity(matrix):
    a=_matrix(matrix)
    return len(a)-len(_reduce(a,len(a))[1])


def inverse(matrix):
    a=_matrix(matrix);n=len(a)
    augmented=[list(row)+[int(i==j) for j in range(n)] for i,row in enumerate(a)]
    reduced,pivots=_reduce(augmented,n)
    if len(pivots)!=n:raise ValueError("matrix is singular")
    return tuple(row[n:] for row in reduced)


def adjugate(matrix):
    a=_matrix(matrix);n=len(a)
    return tuple(tuple((-1)**(i+j)*_det([row[:i]+row[i+1:] for k,row in enumerate(a) if k!=j]) for j in range(n)) for i in range(n))


def solve(matrix,rhs):
    a=_matrix(matrix);n=len(a)
    if type(rhs) not in (list, tuple):raise TypeError("rhs must be a list or tuple")
    if len(rhs)!=n:raise ValueError("rhs size mismatch")
    b=tuple(_entry(x) for x in rhs)
    reduced,pivots=_reduce([list(row)+[b[i]] for i,row in enumerate(a)],n)
    if len(pivots)!=n:raise ValueError("matrix is singular")
    return tuple(row[-1] for row in reduced)


def trace(matrix):
    a=_matrix(matrix)
    return sum(row[i] for i,row in enumerate(a))


def gram_matrix(matrix):
    a=_matrix(matrix);n=len(a)
    return tuple(tuple(sum(a[k][i]*a[k][j] for k in range(n)) for j in range(n)) for i in range(n))


def rref(matrix):
    a=_matrix(matrix)
    return _reduce(a,len(a))[0]
