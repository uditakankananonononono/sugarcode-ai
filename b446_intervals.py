"""Bounded exact closed rational interval arithmetic.

SCOPE: caller-supplied pairs of int/Fraction endpoints of magnitude <=100.
NOT_CLAIMED: floating rounding, unbounded intervals, retrieval, integration.
"""
from fractions import Fraction

CLAIMS = False
SCOPE = "bounded closed rational intervals, exact arithmetic only"
NOT_CLAIMED = "floating rounding, unbounded intervals, retrieval, product integration"
MAX_MAGNITUDE = 100
MAX_DENOMINATOR = 100
MAX_EXPONENT = 8


def _number(x):
    if isinstance(x,bool):
        raise TypeError("endpoint must be int or Fraction")
    if not isinstance(x,(int,Fraction)):
        raise TypeError("endpoint must be int or Fraction")
    if abs(x)>MAX_MAGNITUDE:
        raise ValueError("endpoint magnitude out of range")
    value = Fraction(x)
    if value.denominator>MAX_DENOMINATOR:
        raise ValueError("endpoint denominator out of range")
    return value


def _interval(value):
    if not isinstance(value,(list,tuple)):
        raise TypeError("interval must be a list or tuple")
    if len(value)!=2:
        raise ValueError("interval must have two endpoints")
    low,high = _number(value[0]),_number(value[1])
    if low>high:
        raise ValueError("interval endpoints out of order")
    return low,high


def _pair(a,b):
    return _interval(a),_interval(b)


def interval_add(a,b):
    (lo,hi),(x,y) = _pair(a,b)
    return lo+x,hi+y


def interval_subtract(a,b):
    (lo,hi),(x,y) = _pair(a,b)
    return lo-y,hi-x


def interval_multiply(a,b):
    (lo,hi),(x,y) = _pair(a,b)
    values = (lo*x,lo*y,hi*x,hi*y)
    return min(values),max(values)


def interval_reciprocal(a):
    lo,hi = _interval(a)
    if lo<=0<=hi:
        raise ValueError("interval contains zero")
    return 1/hi,1/lo


def interval_divide(a,b):
    (lo,hi),(x,y) = _pair(a,b)
    if x<=0<=y:
        raise ValueError("interval contains zero")
    values = (lo/x,lo/y,hi/x,hi/y)
    return min(values),max(values)


def interval_intersection(a,b):
    (lo,hi),(x,y) = _pair(a,b)
    low,high = max(lo,x),min(hi,y)
    return (low,high) if low<=high else None


def interval_hull(a,b):
    (lo,hi),(x,y) = _pair(a,b)
    return min(lo,x),max(hi,y)


def interval_absolute(a):
    lo,hi = _interval(a)
    if lo>=0:
        return lo,hi
    if hi<=0:
        return -hi,-lo
    return Fraction(0),max(-lo,hi)


def interval_power(a,exponent):
    lo,hi = _interval(a)
    if isinstance(exponent,bool):
        raise TypeError("exponent must be an integer")
    if not isinstance(exponent,int):
        raise TypeError("exponent must be an integer")
    if exponent<0 or exponent>MAX_EXPONENT:
        raise ValueError("exponent out of range")
    if exponent==0:
        return Fraction(1),Fraction(1)
    values = [lo**exponent,hi**exponent]
    if exponent%2==0 and lo<=0<=hi:
        values.append(Fraction(0))
    return min(values),max(values)


def interval_width(a):
    lo,hi = _interval(a)
    return hi-lo
