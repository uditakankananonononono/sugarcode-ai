"""Bounded exact integer-sequence arithmetic.

SCOPE: caller integer indices up to 40 and small integer recurrences.
NOT_CLAIMED: asymptotics, big-index computation, generating-function theory, integration.
"""
CLAIMS=False
SCOPE="exact bounded classical integer sequences and linear recurrences"
NOT_CLAIMED="asymptotics, big-index computation, generating-function theory, integration"
MAX_N=40
MAX_MOD=64
MAX_ORDER=8
MAX_COEF=100


def _int(x,name,lo,hi):
    if isinstance(x,bool):raise TypeError(name+" must be an integer")
    if not isinstance(x,int):raise TypeError(name+" must be an integer")
    if x<lo or x>hi:raise ValueError(name+" out of range")
    return x


def _n(x):return _int(x,"n",0,MAX_N)


def fibonacci(n):
    n=_n(n);a,b=0,1
    for _ in range(n):a,b=b,a+b
    return a


def lucas(n):
    n=_n(n);a,b=2,1
    for _ in range(n):a,b=b,a+b
    return a


def pisano_period(modulus):
    k=_int(modulus,"modulus",1,MAX_MOD)
    if k==1:return 1
    a,b,p=0,1,0
    while True:
        a,b=b,(a+b)%k;p+=1
        if a==0 and b==1:return p


def catalan(n):
    n=_n(n);c=1
    for i in range(n):c=c*2*(2*i+1)//(i+2)
    return c


def stirling2(n,k):
    n=_n(n);k=_int(k,"k",0,MAX_N)
    row=[1]+[0]*k
    for i in range(1,n+1):
        row=[0]+[j*row[j]+row[j-1] for j in range(1,k+1)]
    return row[k]


def stirling1_unsigned(n,k):
    n=_n(n);k=_int(k,"k",0,MAX_N)
    row=[1]+[0]*k
    for i in range(1,n+1):
        row=[0]+[(i-1)*row[j]+row[j-1] for j in range(1,k+1)]
    return row[k]


def bell(n):
    n=_n(n);row=[1]
    for _ in range(n):
        nxt=[row[-1]]
        for x in row:nxt.append(nxt[-1]+x)
        row=nxt
    return row[0]


def motzkin(n):
    n=_n(n);a,b=1,1
    if n==0:return 1
    for i in range(2,n+1):a,b=b,((2*i+1)*b+(3*i-3)*a)//(i+2)
    return b


def delannoy(m,n):
    m=_int(m,"m",0,MAX_N);n=_int(n,"n",0,MAX_N)
    row=[1]*(n+1)
    for _ in range(m):
        new=[1]
        for j in range(1,n+1):new.append(new[j-1]+row[j]+row[j-1])
        row=new
    return row[n]


def linear_recurrence_term(coefficients,initial,n):
    if not isinstance(coefficients,(list,tuple)):raise TypeError("coefficients must be a list or tuple")
    if not isinstance(initial,(list,tuple)):raise TypeError("initial must be a list or tuple")
    if not 1<=len(coefficients)<=MAX_ORDER:raise ValueError("order out of range")
    if len(initial)!=len(coefficients):raise ValueError("initial length must equal order")
    for x in coefficients:_int(x,"coefficient",-MAX_COEF,MAX_COEF)
    for x in initial:_int(x,"initial value",-MAX_COEF,MAX_COEF)
    n=_n(n)
    seq=list(initial)
    while len(seq)<=n:
        seq.append(sum(c*seq[-1-i] for i,c in enumerate(coefficients)))
    return seq[n]
