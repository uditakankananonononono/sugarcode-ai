"""Bounded exact simple continued fractions of rationals.

SCOPE: caller rationals num/den with |num|<=10**6 and 1<=den<=10**6, term lists of 1..32 integers
(|term|<=10**6, terms after the first positive), exact int arithmetic only.
ADJACENT: Atlas 298fe826 and Sugarcode dfb0a002 screened for continued fraction, Bezout, extended gcd, Stern-Brocot: no implementation found. extended_gcd is the Euclid/Bezout recurrence that the expansion shares by definition; no code shared. Farey and Pell expansions are deliberately not included.
NOT_CLAIMED: irrational or periodic expansions, floating approximation, units, integration.
"""
CLAIMS=False
SCOPE="exact bounded simple continued fraction arithmetic over rationals"
NOT_CLAIMED="irrational or periodic expansions, floating approximation, units, integration"
MAX_VALUE=10**6
MAX_TERMS=32
MAX_TERM=10**6


def _int(x,name,lo,hi):
    if type(x) is not int:raise TypeError(name+" must be an integer")
    if x<lo or x>hi:raise ValueError(name+" out of range")
    return x


def _rational(num,den):
    return _int(num,"numerator",-MAX_VALUE,MAX_VALUE),_int(den,"denominator",1,MAX_VALUE)


def _terms(terms):
    if type(terms) not in (list,tuple):raise TypeError("terms must be a list or tuple")
    if not 1<=len(terms)<=MAX_TERMS:raise ValueError("term count out of range")
    out=[_int(t,"term",-MAX_TERM,MAX_TERM) for t in terms]
    if any(t<1 for t in out[1:]):raise ValueError("terms after the first must be positive")
    return out


def _expand(num,den):
    out=[]
    while den:
        q=num//den
        out.append(q);num,den=den,num-q*den
    return out


def _convergents(terms):
    p0,q0,p1,q1=1,0,terms[0],1
    out=[(p1,q1)]
    for a in terms[1:]:
        p0,q0,p1,q1=p1,q1,a*p1+p0,a*q1+q0
        out.append((p1,q1))
    return out


def cf_expand(num,den):
    n,d=_rational(num,den)
    return tuple(_expand(n,d))


def cf_value(terms):
    p,q=_convergents(_terms(terms))[-1]
    return (p,q)


def convergents(terms):
    return tuple(_convergents(_terms(terms)))


def is_canonical(terms):
    t=_terms(terms)
    return len(t)==1 or t[-1]>1


def semiconvergents(terms):
    t=_terms(terms)
    out=[(t[0],1)]
    p0,q0,p1,q1=1,0,t[0],1
    for a in t[1:]:
        for s in range(1,a+1):out.append((s*p1+p0,s*q1+q0))
        p0,q0,p1,q1=p1,q1,a*p1+p0,a*q1+q0
    return tuple(out)


def best_approximation(num,den,max_den):
    n,d=_rational(num,den);bound=_int(max_den,"max_den",1,MAX_VALUE)
    t=_expand(n,d)
    best=None
    p0,q0,p1,q1=1,0,t[0],1
    cands=[(p1,q1)] if q1<=bound else []
    for a in t[1:]:
        s=min(a,(bound-q0)//q1)
        if s>=1:cands.append((s*p1+p0,s*q1+q0))
        if s<a:break
        p0,q0,p1,q1=p1,q1,a*p1+p0,a*q1+q0
    for p,q in cands:
        if best is None or abs(n*q-p*d)*best[1]<abs(n*best[1]-best[0]*d)*q:best=(p,q)
    return best


def cf_compare(terms1,terms2):
    a=_terms(terms1);b=_terms(terms2)
    if not (len(a)==1 or a[-1]>1) or not (len(b)==1 or b[-1]>1):raise ValueError("terms must be canonical")
    for i in range(max(len(a),len(b))):
        x=a[i] if i<len(a) else None;y=b[i] if i<len(b) else None
        if x==y:continue
        # a missing term is +infinity
        if x is None:less=False
        elif y is None:less=True
        else:less=x<y
        if i%2:less=not less
        return -1 if less else 1
    return 0


def cf_negate(terms):
    a=_terms(terms)
    if not (len(a)==1 or a[-1]>1):raise ValueError("terms must be canonical")
    if len(a)==1:return (-a[0],)
    if a[1]==1:return tuple([-a[0]-1,a[2]+1]+a[3:])
    if len(a)==2 and a[1]==2:return (-a[0]-1,2)
    return tuple([-a[0]-1,1,a[1]-1]+a[2:])


def extended_gcd(a,b):
    x=_int(a,"a",0,MAX_VALUE);y=_int(b,"b",0,MAX_VALUE)
    if x==0 and y==0:raise ValueError("a and b must not both be zero")
    if y==0:return (x,1,0)
    r0,r1,s0,s1=x,y,1,0
    while r1:
        q=r0//r1
        r0,r1,s0,s1=r1,r0-q*r1,s1,s0-q*s1
    g=r0;s0%=y//g
    return (g,s0,(g-x*s0)//y)


def euclid_step_count(a,b):
    x=_int(a,"a",0,MAX_VALUE);y=_int(b,"b",0,MAX_VALUE)
    if x==0 and y==0:raise ValueError("a and b must not both be zero")
    n=0
    while y:
        x,y=y,x%y;n+=1
    return n
