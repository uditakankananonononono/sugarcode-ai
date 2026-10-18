"""Abstract signed tooth-ratio chains, rational-constraint adjacency.

Caller teeth exacttuple length2..8 exactints1..40; signs exacttuple n-1
entries -1/+1. Model equation teeth[i+1]*speed[i+1] =
signs[i]*teeth[i]*speed[i]. No engineering or physical validity claim.
Ten operations share one rational chain family, not ten independent ideas.
"""
from fractions import Fraction
from math import lcm
SCOPE='PARTIAL abstract signed tooth-ratio chain fixtures, rational-constraint adjacency disclosed'
NOT_CLAIMED=('AGI-like intelligence','engineering validity','physical mechanism feasibility','power or load analysis','production readiness')
CLAIMS={'agi_like_intelligence':False,'engineering_validity':False,'production_ready':False}


def _fail(c):raise ValueError('G502:'+c)


def _chain(teeth,signs):
    if type(teeth)is not tuple:_fail('type:teeth')
    if not 2<=len(teeth)<=8:_fail('length:teeth')
    if any(type(x)is not int for x in teeth):_fail('type:tooth')
    if any(not 1<=x<=40 for x in teeth):_fail('bound:tooth')
    if type(signs)is not tuple or len(signs)!=len(teeth)-1:_fail('shape:signs')
    if any(type(x)is not int for x in signs):_fail('type:sign')
    if any(x not in (-1,1) for x in signs):_fail('bound:sign')


def _integer(x,lo,hi,label):
    if type(x)is not int:_fail('type:'+label)
    if not lo<=x<=hi:_fail('bound:'+label)


def _ratios(teeth,signs):
    result=[Fraction(1)]
    for i,s in enumerate(signs):result.append(result[-1]*s*teeth[i]/teeth[i+1])
    return tuple(result)


def ratio_vector(teeth,signs):
    _chain(teeth,signs);return _ratios(teeth,signs)


def velocity_vector(teeth,signs,drive):
    _chain(teeth,signs);_integer(drive,-20,20,'drive')
    return tuple(drive*r for r in _ratios(teeth,signs))


def primitive_turn_cycle(teeth,signs):
    _chain(teeth,signs);ratios=_ratios(teeth,signs);period=lcm(*(r.denominator for r in ratios))
    return period,tuple(int(period*r) for r in ratios)


def signed_tooth_products(teeth,signs):
    _chain(teeth,signs);return tuple(t*r for t,r in zip(teeth,_ratios(teeth,signs)))


def reverse_chain_certificate(teeth,signs):
    _chain(teeth,signs);forward=_ratios(teeth,signs);back=_ratios(teeth[::-1],signs[::-1])
    return tuple(back[i]*forward[-1] for i in range(len(teeth)))==forward[::-1]


def pair_transfer(teeth,signs,source,destination):
    _chain(teeth,signs);_integer(source,0,len(teeth)-1,'source');_integer(destination,0,len(teeth)-1,'destination')
    ratios=_ratios(teeth,signs);return ratios[destination]/ratios[source]


def closure_residual(teeth,signs,closing_sign):
    """Residual for a supplied last-to-first edge;zero means algebraic closure."""
    _chain(teeth,signs);_integer(closing_sign,-1,1,'closing_sign')
    if closing_sign==0:_fail('zero:closing_sign')
    return teeth[0]-closing_sign*teeth[-1]*_ratios(teeth,signs)[-1]


def synchronized_pairs(teeth,signs):
    _chain(teeth,signs);ratios=_ratios(teeth,signs)
    return tuple((i,j) for i in range(len(teeth)) for j in range(i+1,len(teeth)) if ratios[i]==ratios[j])


def integer_drive_options(teeth,signs,cap):
    _chain(teeth,signs);_integer(cap,0,20,'cap');ratios=_ratios(teeth,signs)
    return tuple(k for k in range(1,cap+1) if all((k*r).denominator==1 for r in ratios))


def phase_return_certificate(teeth,signs,turns):
    _chain(teeth,signs);_integer(turns,0,100,'turns')
    return all((turns*r).denominator==1 for r in _ratios(teeth,signs))
