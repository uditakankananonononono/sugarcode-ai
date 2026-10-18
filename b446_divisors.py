"""Bounded exact divisor-incidence arithmetic on integers 1..64.

SCOPE: caller integers and length<=64 integer arithmetic-function vectors.
NOT_CLAIMED: factorization at scale, cryptography, prime-power models, integration.
"""
from math import gcd
CLAIMS=False
SCOPE="exact bounded positive-integer divisor and incidence arithmetic"
NOT_CLAIMED="factorization at scale, cryptography, prime-power models, integration"
MAX_N=64
MAX_ENTRY=100


def _n(x):
    if isinstance(x,bool):raise TypeError("n must be an integer")
    if not isinstance(x,int):raise TypeError("n must be an integer")
    if x<1 or x>MAX_N:raise ValueError("n out of range")
    return x


def _divisors(n):return tuple(d for d in range(1,n+1) if n%d==0)


def _mobius(n):
    factors=0;d=2
    while d*d<=n:
        if n%d==0:
            n//=d;factors+=1
            if n%d==0:return 0
        while n%d==0:n//=d
        d+=1
    if n>1:factors+=1
    return (-1)**factors


def _vector(values):
    if not isinstance(values,(list,tuple)):raise TypeError("values must be a list or tuple")
    if not 1<=len(values)<=MAX_N:raise ValueError("vector size out of range")
    for x in values:
        if isinstance(x,bool):raise TypeError("entry must be an integer")
        if not isinstance(x,int):raise TypeError("entry must be an integer")
        if abs(x)>MAX_ENTRY:raise ValueError("entry out of range")
    return tuple(values)


def divisors(n):return _divisors(_n(n))


def divisor_count(n):return len(_divisors(_n(n)))


def divisor_sum(n):return sum(_divisors(_n(n)))


def mobius(n):return _mobius(_n(n))


def totient(n):
    n=_n(n)
    return sum(gcd(k,n)==1 for k in range(1,n+1))


def jordan_totient_two(n):
    n=_n(n)
    return sum(_mobius(d)*(n//d)**2 for d in _divisors(n))


def ramanujan_sum(n,k):
    """Integer Ramanujan sum c_n(k), including k=0 and negative k."""
    n=_n(n)
    if isinstance(k,bool):raise TypeError("k must be an integer")
    if not isinstance(k,int):raise TypeError("k must be an integer")
    if abs(k)>MAX_N:raise ValueError("k out of range")
    return sum(d*_mobius(n//d) for d in _divisors(gcd(n,k)))


def divisor_zeta(values):
    a=_vector(values)
    return tuple(sum(a[d-1] for d in _divisors(n)) for n in range(1,len(a)+1))


def divisor_mobius_inverse(values):
    a=_vector(values)
    return tuple(sum(_mobius(n//d)*a[d-1] for d in _divisors(n)) for n in range(1,len(a)+1))


def dirichlet_convolution(left,right):
    a,b=_vector(left),_vector(right)
    if len(a)!=len(b):raise ValueError("vector sizes must agree")
    return tuple(sum(a[d-1]*b[n//d-1] for d in _divisors(n)) for n in range(1,len(a)+1))
