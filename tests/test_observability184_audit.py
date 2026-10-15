import copy,itertools as it,random,unittest
from fractions import Fraction as F
from sugarcode.extra_doc import observability184 as m
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class D(dict):pass

def mm(a,b):return [[sum(a[i][k]*b[k][j] for k in (0,1)) for j in (0,1)] for i in (0,1)]
def power(a,k):
    r=[[1,0],[0,1]]
    while k:
        if k&1:r=mm(r,a)
        a=mm(a,a);k//=2
    return r

def oracle(d):
    rows=[]
    for k in range(d['horizon']):
        p=power(d['matrix'],k);rows.append([sum(d['sensor'][i]*p[i][j] for i in (0,1)) for j in (0,1)])
    g=[[sum(r[i]*r[j] for r in rows) for j in (0,1)] for i in (0,1)]
    rank=2 if any(a*d-b*c for (a,b),(c,d) in it.combinations(rows,2)) else int(any(any(r) for r in rows))
    assert (g[0][0]*g[1][1]-g[0][1]*g[1][0]!=0)==(rank==2)
    if rank==0:basis=[[F(1),F(0)],[F(0),F(1)]]
    elif rank==2:basis=[]
    else:
        a,b=next(r for r in rows if any(r));v=[F(-b),F(a)];scale=v[1] if v[1] else v[0];basis=[[x/scale for x in v]]
    return dict(observations=rows,gramian=g,rank=rank,unobservable_basis=[[[x.numerator,x.denominator] for x in v] for v in basis],claims=[False]*3)

def exact(a,b):
    assert type(a) is type(b),(a,b)
    if type(b) is dict:
        assert list(a)==list(b)
        for k in b:exact(a[k],b[k])
    elif type(b) in (list,tuple):
        assert len(a)==len(b)
        for x,y in zip(a,b):exact(x,y)
    else:assert a==b,(a,b)

def check(d):
    old=copy.deepcopy(d)
    try:r=m.analyze(d)
    finally:assert d==old
    exact(r,oracle(d))
    r['observations'][0][0]=999
    assert d==old

def good():return dict(matrix=[[-2,2],[2,-2]],sensor=[-2,2],horizon=5)
def fail(d,msg):
    old=copy.deepcopy(d)
    try:m.analyze(d)
    except ValueError as e:assert str(e)==msg,(str(e),msg)
    else:raise AssertionError('accepted')
    finally:assert d==old

class Quick(unittest.TestCase):
    def test_pins(self):
        exact(m.SCOPE,'PARTIAL: exact supplied two-state finite-horizon observability matrix and nullspace only')
        exact(m.NOT_CLAIMED,('identified real dynamics','noisy state estimation','production readiness'))
    def test_valid(self):
        rng=random.Random(184230)
        for _ in range(120):check(dict(matrix=[[rng.randint(-2,2) for j in range(2)] for i in range(2)],sensor=[rng.randint(-2,2) for i in range(2)],horizon=rng.randint(1,5)))
        for a in ([[0,0],[0,0]],[[1,0],[0,1]],[[1,1],[0,1]],[[-2,2],[2,-2]]):
            for c in it.product((-2,0,2),repeat=2):
                for h in (1,5):check(dict(matrix=a,sensor=list(c),horizon=h))
    def test_invalid(self):
        outer='exact dict with matrix, sensor, horizon required';matrix='matrix must be an exact two-row list';row='matrix row must be an exact two-item list';entry='matrix entries must be exact integers -2..2';sensor='sensor must be an exact two-item list';cell='sensor entries must be exact integers -2..2';horizon='horizon must be an exact integer 1..5'
        aliens=[None,True,I(0),0.0,S('x'),'x',T(()),D(),L()]
        for v in aliens+[{},D(good()),dict(good(),extra=1)]:fail(v,outer)
        for field,msg in [('matrix',matrix),('sensor',sensor)]:
            for v in aliens+[[],[0],[0]*3,L([0,0]),(0,0)]:
                d=good();d[field]=v;fail(d,msg)
        for i in range(2):
            for v in aliens+[[],[0],[0]*3,L([0,0]),(0,0)]:
                d=good();d['matrix'][i]=v;fail(d,row)
            for j in range(2):
                for v in aliens+[-3,3]:
                    d=good();d['matrix'][i][j]=v;fail(d,entry)
            for v in aliens+[-3,3]:
                d=good();d['sensor'][i]=v;fail(d,cell)
        for v in aliens+[0,6]:
            d=good();d['horizon']=v;fail(d,horizon)
        fail(dict(matrix=[[None,0],None],sensor=None,horizon=None),entry)
        fail(dict(matrix=[[0,0],None],sensor=[None,0],horizon=None),row)
        fail(dict(matrix=[[0,0],[0,0]],sensor=[None,0],horizon=None),cell)

class Exhaustive(unittest.TestCase):
    def test_all_valid_domain(self):
        for entries in it.product(range(-2,3),repeat=4):
            a=[list(entries[:2]),list(entries[2:])]
            for c in it.product(range(-2,3),repeat=2):
                for h in range(1,6):check(dict(matrix=a,sensor=list(c),horizon=h))
