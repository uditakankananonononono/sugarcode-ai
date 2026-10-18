"""Exact bounded octonion fixtures, adjacent to existing quaternion family.

New content is nonassociative 8-coordinate Cayley-Dickson arithmetic and
associator/alternativity/Moufang certificates, not new quaternion credit.
Octonions are exact tuples of8 exact ints with abs<=8. Rational outputs
use Fraction; no floats. Convention(a,b)(c,d)=(ac-conj(d)b, da+b conj(c))
for quaternion halves a,b,c,d in Hamilton(1,i,j,k) order. All arguments
validated before arithmetic. Three product inputs bounded8 ensure outputs
remain exact small integers. No geometry, physical algebra or AGI claim.
"""
from fractions import Fraction
SCOPE='PARTIAL bounded exact octonion nonassociativity fixtures, quaternion adjacency disclosed'
NOT_CLAIMED=('AGI-like intelligence','new quaternion algebra','geometric validity','production readiness')
CLAIMS={'agi_like_intelligence':False,'production_ready':False,'geometric_validity':False}


def _fail(code):raise ValueError('O492:'+code)


def _inputs(*values):
    if any(type(v)is not tuple or len(v)!=8 for v in values):_fail('shape:octonion')
    if any(type(x)is not int for v in values for x in v):_fail('type:coordinate')
    if any(abs(x)>8 for v in values for x in v):_fail('bound:coordinate')


def _qconj(a):return (a[0],-a[1],-a[2],-a[3])


def _qmul(a,b):
    r,x,y,z=a;s,u,v,w=b
    return (r*s-x*u-y*v-z*w,r*u+x*s+y*w-z*v,r*v-x*w+y*s+z*u,r*w+x*v-y*u+z*s)


def _mul(x,y):
    a,b=x[:4],x[4:];c,d=y[:4],y[4:]
    ac=_qmul(a,c);db=_qmul(_qconj(d),b);da=_qmul(d,a);bc=_qmul(b,_qconj(c))
    return tuple(v-w for v,w in zip(ac,db))+tuple(v+w for v,w in zip(da,bc))


def _conj(x):return (x[0],)+tuple(-v for v in x[1:])


def _norm(x):return sum(v*v for v in x)


def _subtract(a,b):return tuple(x-y for x,y in zip(a,b))


def octonion_multiply(left,right):
    _inputs(left,right);return _mul(left,right)


def octonion_conjugate(value):
    _inputs(value);return _conj(value)


def octonion_norm_squared(value):
    _inputs(value);return _norm(value)


def octonion_inverse(value):
    _inputs(value);norm=_norm(value)
    if not norm:_fail('zero:inverse')
    return tuple(Fraction(x,norm) for x in _conj(value))


def octonion_associator(first,second,third):
    """(first*second)*third-first*(second*third)."""
    _inputs(first,second,third)
    return _subtract(_mul(_mul(first,second),third),_mul(first,_mul(second,third)))


def octonion_commutator(left,right):
    _inputs(left,right);return _subtract(_mul(left,right),_mul(right,left))


def octonion_left_matrix(value):
    """8x8 integer linear map columns value*e_j, rows output coordinates."""
    _inputs(value)
    columns=[_mul(value,tuple(int(i==j) for i in range(8))) for j in range(8)]
    return tuple(tuple(col[i] for col in columns) for i in range(8))


def octonion_right_divide(numerator,denominator):
    """Unique x satisfying x*denominator=numerator; x=numerator*inverse(d)."""
    _inputs(numerator,denominator);norm=_norm(denominator)
    if not norm:_fail('zero:denominator')
    product=_mul(numerator,_conj(denominator))
    return tuple(Fraction(x,norm) for x in product)


def octonion_alternativity_certificate(left,right):
    """Return L/R alternative residuals and flexible residual, all zero."""
    _inputs(left,right)
    a=_subtract(_mul(_mul(left,left),right),_mul(left,_mul(left,right)))
    b=_subtract(_mul(_mul(right,left),left),_mul(right,_mul(left,left)))
    c=_subtract(_mul(_mul(left,right),left),_mul(left,_mul(right,left)))
    return a,b,c


def octonion_moufang_certificate(first,second,third):
    """Return exact pair((xy)(zx), x((yz)x)); identical by Moufang identity."""
    _inputs(first,second,third)
    return _mul(_mul(first,second),_mul(third,first)),_mul(first,_mul(_mul(second,third),first))
