"""Bounded exact transferable-utility characteristic-game arithmetic.

SCOPE: n<=5 players; 2**n caller-supplied integer coalition values -100..100.
NOT_CLAIMED: empirical valuation, mechanism design, optimization, integration.
"""
from fractions import Fraction
from math import factorial

CLAIMS = False
SCOPE = "exact caller-supplied finite characteristic vectors only"
NOT_CLAIMED = "empirical valuation, mechanism design, optimization, product integration"
MAX_PLAYERS = 5
MAX_VALUE = 100


def _int(x,name,low,high):
    if isinstance(x,bool):raise TypeError(name+" must be an integer")
    if type(x) is not int:raise TypeError(name+" must be an integer")
    if x<low or x>high:raise ValueError(name+" out of range")
    return x


def _vector(n,values):
    _int(n,'players',0,MAX_PLAYERS)
    if type(values) not in (list,tuple):raise TypeError("values must be a list or tuple")
    if len(values)!=1<<n:raise ValueError("values size mismatch")
    out=tuple(_int(x,'value',-MAX_VALUE,MAX_VALUE) for x in values)
    if out[0]!=0:raise ValueError("empty coalition must have value zero")
    return out


def coalition_value(n,values,mask):
    data=_vector(n,values)
    _int(mask,'mask',0,(1<<n)-1)
    return data[mask]


def marginal_contribution(n,values,mask,player):
    data=_vector(n,values)
    _int(mask,'mask',0,(1<<n)-1)
    _int(player,'player',0,n-1)
    if mask>>player&1:raise ValueError("player already in coalition")
    return data[mask|1<<player]-data[mask]


def shapley_values(n,values):
    data=_vector(n,values)
    out=[]
    for i in range(n):
        value=Fraction(0)
        for mask in range(1<<n):
            if not mask>>i&1:
                size=mask.bit_count()
                value+=Fraction(factorial(size)*factorial(n-size-1),factorial(n))*(data[mask|1<<i]-data[mask])
        out.append(value)
    return tuple(out)


def banzhaf_values(n,values):
    data=_vector(n,values)
    return tuple(Fraction(sum(data[mask|1<<i]-data[mask] for mask in range(1<<n) if not mask>>i&1),1<<(n-1)) for i in range(n))


def mobius_dividends(n,values):
    data=list(_vector(n,values))
    for i in range(n):
        for mask in range(1<<n):
            if mask>>i&1:data[mask]-=data[mask^(1<<i)]
    return tuple(data)


def reconstruct_values(n,dividends):
    """Inverse transform; dividends obey the same input cap as values."""
    data=list(_vector(n,dividends))
    for i in range(n):
        for mask in range(1<<n):
            if mask>>i&1:data[mask]+=data[mask^(1<<i)]
    return tuple(data)


def dual_values(n,values):
    data=_vector(n,values);full=(1<<n)-1
    return tuple(data[full]-data[full^mask] for mask in range(1<<n))


def is_monotone(n,values):
    data=_vector(n,values)
    return all(data[mask]<=data[mask|1<<i] for mask in range(1<<n) for i in range(n) if not mask>>i&1)


def is_superadditive(n,values):
    data=_vector(n,values)
    return all(data[a]+data[b]<=data[a|b] for a in range(1<<n) for b in range(1<<n) if not a&b)


def efficiency_gap(n,values,allocation):
    """Grand-coalition value minus the sum of a bounded rational allocation."""
    data=_vector(n,values)
    if type(allocation) not in (list,tuple):raise TypeError("allocation must be a list or tuple")
    if len(allocation)!=n:raise ValueError("allocation size mismatch")
    for x in allocation:
        if isinstance(x,bool):raise TypeError("allocation must be int or Fraction")
        if type(x) not in (int,Fraction):raise TypeError("allocation must be int or Fraction")
        if abs(x)>MAX_VALUE:raise ValueError("allocation magnitude out of range")
        if Fraction(x).denominator>100:raise ValueError("allocation denominator out of range")
    return Fraction(data[-1])-sum(allocation,Fraction(0))
