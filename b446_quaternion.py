"""Bounded exact rational Hamilton quaternion arithmetic.

SCOPE: caller supplied four-tuples, rational magnitude<=10, denominators<=10.
NOT_CLAIMED: floating geometry, 3D engine integration, retrieval, unit-only rotation.
"""
from fractions import Fraction
CLAIMS=False
SCOPE="bounded exact rational Hamilton quaternion and conjugation arithmetic"
NOT_CLAIMED="floating geometry, 3D engine integration, retrieval, unit-only rotation"
MAX_MAGNITUDE=10
MAX_DENOMINATOR=10
MAX_EXPONENT=8


def _scalar(x):
    if type(x) not in (int, Fraction):raise TypeError("component must be int or Fraction")
    if abs(x)>MAX_MAGNITUDE:raise ValueError("component magnitude out of range")
    x=Fraction(x)
    if x.denominator>MAX_DENOMINATOR:raise ValueError("component denominator out of range")
    return x


def _tuple(x,size,name):
    if type(x) not in (list, tuple):raise TypeError(name+" must be a list or tuple")
    if len(x)!=size:raise ValueError(name+" size mismatch")
    return tuple(_scalar(y) for y in x)


def _q(x):return _tuple(x,4,'quaternion')


def _mul(a,b):
    w,x,y,z=a;v,i,j,k=b
    return (w*v-x*i-y*j-z*k,w*i+x*v+y*k-z*j,w*j-x*k+y*v+z*i,w*k+x*j-y*i+z*v)


def _conj(a):return (a[0],-a[1],-a[2],-a[3])


def _inverse(a):
    norm=sum(x*x for x in a)
    if norm==0:raise ValueError("quaternion must be nonzero")
    return tuple(x/norm for x in _conj(a))


def add(a,b):
    a,b=_q(a),_q(b)
    return tuple(x+y for x,y in zip(a,b))


def subtract(a,b):
    a,b=_q(a),_q(b)
    return tuple(x-y for x,y in zip(a,b))


def multiply(a,b):
    a,b=_q(a),_q(b)
    return _mul(a,b)


def conjugate(a):return _conj(_q(a))


def norm_squared(a):return sum(x*x for x in _q(a))


def inverse(a):return _inverse(_q(a))


def divide(a,b):
    a,b=_q(a),_q(b)
    return _mul(a,_inverse(b))


def commutator(a,b):
    a,b=_q(a),_q(b)
    ab,ba=_mul(a,b),_mul(b,a)
    return tuple(x-y for x,y in zip(ab,ba))


def integer_power(a,exponent):
    a=_q(a)
    if type(exponent) is not int:raise TypeError("exponent must be an integer")
    if exponent<0 or exponent>MAX_EXPONENT:raise ValueError("exponent out of range")
    result=(Fraction(1),Fraction(0),Fraction(0),Fraction(0))
    for _ in range(exponent):result=_mul(result,a)
    return result


def rotate_vector(a,vector):
    """Conjugation rotation for any nonzero rational quaternion, not just units."""
    a=_q(a);v=_tuple(vector,3,'vector')
    return _mul(_mul(a,(Fraction(0),)+v),_inverse(a))[1:]
