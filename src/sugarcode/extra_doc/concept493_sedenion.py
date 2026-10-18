"""Bounded exact sedenion zero-divisor/failure certificates.

Adjacent b492 octonion arithmetic is NOT claimed anew. New focus: failure
of division, norm composition, alternativity and Moufang beyond octonions.
Inputs exact tuple16 exact integers abs<=2. Kernel bases are Fraction tuples
in deterministic free-column order from reduced row echelon elimination.
Cayley-Dickson convention(a,b)(c,d)=(ac-conj(d)b,da+b conj(c)).
Zero-divisor search only over signed sums e_i +/- e_j, i<j, all120pairs
and2signs; None means no witness in this finite catalogue, NOT invertibility.
No retrieval/network, no geometric/physical/AGI/production claims.
"""
from fractions import Fraction as F
from itertools import combinations
SCOPE='PARTIAL sedenion zero-divisor and failed-composition certificates, adjacent octonions disclosed'
NOT_CLAIMED=('AGI-like intelligence','new octonion arithmetic','global zero-divisor decision','physical validity','production readiness')
CLAIMS={'agi_like_intelligence':False,'production_ready':False,'global_zero_divisor_decision':False}


def _fail(code):raise ValueError('S493:'+code)


def _inputs(*vs):
    if any(type(v)is not tuple or len(v)!=16 for v in vs):_fail('shape:sedenion')
    if any(type(x)is not int for v in vs for x in v):_fail('type:coordinate')
    if any(abs(x)>2 for v in vs for x in v):_fail('bound:coordinate')


def _conj(a):return (a[0],)+tuple(-x for x in a[1:])


def _mul(x,y):
    if len(x)==1:return (x[0]*y[0],)
    h=len(x)//2;a,b=x[:h],x[h:];c,d=y[:h],y[h:]
    ac=_mul(a,c);db=_mul(_conj(d),b);da=_mul(d,a);bc=_mul(b,_conj(c))
    return tuple(v-w for v,w in zip(ac,db))+tuple(v+w for v,w in zip(da,bc))


def _norm(a):return sum(x*x for x in a)


def _sub(a,b):return tuple(x-y for x,y in zip(a,b))


def _matrix(value,left):
    cols=[_mul(value,e) if left else _mul(e,value) for e in (tuple(int(i==j) for i in range(16)) for j in range(16))]
    return tuple(tuple(c[i] for c in cols) for i in range(16))


def _kernel(matrix):
    rows=[list(map(F,row)) for row in matrix];pivots=[];r=0
    for c in range(16):
        pivot=next((i for i in range(r,16) if rows[i][c]),None)
        if pivot is None:continue
        rows[r],rows[pivot]=rows[pivot],rows[r];value=rows[r][c];rows[r]=[v/value for v in rows[r]]
        for i in range(16):
            if i!=r:
                value=rows[i][c];rows[i]=[v-value*w for v,w in zip(rows[i],rows[r])]
        pivots.append(c);r+=1
    result=[]
    for free in range(16):
        if free in pivots:continue
        v=[F(0)]*16;v[free]=F(1)
        for row,c in enumerate(pivots):v[c]=-rows[row][free]
        result.append(tuple(v))
    return tuple(result)


def zero_product_certificate(left,right):
    """Return(product,is nontrivial zero product), not a yes/no heuristic."""
    _inputs(left,right);product=_mul(left,right)
    return product,bool(any(left) and any(right) and not any(product))


def left_kernel_basis(value):
    """Basis of x with value*x=0 (left multiplication map kernel)."""
    _inputs(value);return _kernel(_matrix(value,True))


def right_kernel_basis(value):
    """Basis of x with x*value=0."""
    _inputs(value);return _kernel(_matrix(value,False))


def left_annihilator_dimension(value):
    """Nullity of left multiplication; shares elimination with basis kernel."""
    _inputs(value);return len(_kernel(_matrix(value,True)))


def right_annihilator_dimension(value):
    _inputs(value);return len(_kernel(_matrix(value,False)))


def norm_defect(left,right):
    """N(left*right)-N(left)N(right), zero is not generally guaranteed."""
    _inputs(left,right);return _norm(_mul(left,right))-_norm(left)*_norm(right)


def alternativity_defect(left,right):
    _inputs(left,right)
    return _sub(_mul(_mul(left,left),right),_mul(left,_mul(left,right))),_sub(_mul(_mul(right,left),left),_mul(right,_mul(left,left)))


def moufang_defect(first,second,third):
    _inputs(first,second,third)
    return _sub(_mul(_mul(first,second),_mul(third,first)),_mul(first,_mul(_mul(second,third),first)))


def _catalogue():
    for i,j in combinations(range(16),2):
        for sign in (-1,1):yield tuple(1 if k==i else sign if k==j else 0 for k in range(16))


def zero_divisor_witness(value):
    """First catalogue v with value*v=0, None for0 or no catalogue witness."""
    _inputs(value)
    if not any(value):return None
    for v in _catalogue():
        if not any(_mul(value,v)):return v
    return None


def signed_basis_pair_zero_divisors(value):
    """All catalogue v annihilated on BOTH sides, empty for zero input.

    Zero excluded deliberately: this enumerates nontrivial divisor fixtures.
    """
    _inputs(value)
    if not any(value):return ()
    return tuple(v for v in _catalogue() if not any(_mul(value,v)) and not any(_mul(v,value)))
