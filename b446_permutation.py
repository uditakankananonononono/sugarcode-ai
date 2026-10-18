"""Exact bounded permutation statistics and Josephus elimination.

SCOPE: caller-supplied permutations n<=8; Josephus n,step<=8.
NOT_CLAIMED: queueing models, randomness, retrieval, product integration.
"""
CLAIMS=False
SCOPE="bounded exact permutation and Josephus arithmetic"
NOT_CLAIMED="queueing models, randomness, retrieval, product integration"
MAX_N=8


def _int(x,name,low,high):
    if isinstance(x,bool):raise TypeError(name+" must be an integer")
    if type(x) is not int:raise TypeError(name+" must be an integer")
    if x<low or x>high:raise ValueError(name+" out of range")
    return x


def _permutation(p):
    if type(p) not in (list,tuple):raise TypeError("permutation must be a list or tuple")
    if len(p)>MAX_N:raise ValueError("permutation size out of range")
    seen=set()
    for x in p:
        _int(x,'entry',0,len(p)-1)
        if x in seen:raise ValueError("entries must be distinct")
        seen.add(x)
    return tuple(p)


def inversion_count(p):
    p=_permutation(p)
    return sum(p[i]>p[j] for i in range(len(p)) for j in range(i+1,len(p)))


def major_index(p):
    p=_permutation(p)
    return sum(i+1 for i in range(len(p)-1) if p[i]>p[i+1])


def descent_count(p):
    p=_permutation(p)
    return sum(p[i]>p[i+1] for i in range(len(p)-1))


def excedance_count(p):
    p=_permutation(p)
    return sum(x>i for i,x in enumerate(p))


def fixed_point_count(p):
    p=_permutation(p)
    return sum(x==i for i,x in enumerate(p))


def cycle_count(p):
    p=_permutation(p);seen=set();count=0
    for i in range(len(p)):
        if i not in seen:
            count+=1;j=i
            while j not in seen:seen.add(j);j=p[j]
    return count


def permutation_sign(p):
    p=_permutation(p)
    return (-1)**inversion_count(p)


def eulerian_number(n,k):
    """Count n-permutations with k descents; A(0,0)=1."""
    _int(n,'n',0,MAX_N);_int(k,'k',0,MAX_N)
    row=[1]+[0]*MAX_N
    for size in range(1,n+1):
        previous=row;row=[0]*(MAX_N+1)
        for j in range(size):
            row[j]=(j+1)*previous[j]+(size-j)*(previous[j-1] if j else 0)
    return row[k]


def josephus_survivor(n,step):
    """Zero-based survivor; n>=1."""
    _int(n,'n',1,MAX_N);_int(step,'step',1,MAX_N)
    survivor=0
    for size in range(2,n+1):survivor=(survivor+step)%size
    return survivor


def josephus_order(n,step):
    """Zero-based elimination order, final survivor last."""
    _int(n,'n',1,MAX_N);_int(step,'step',1,MAX_N)
    alive=list(range(n));index=0;out=[]
    while alive:
        index=(index+step-1)%len(alive)
        out.append(alive.pop(index))
    return tuple(out)
