from fractions import Fraction as F
from itertools import permutations
from copy import deepcopy
import random
import pytest
from sugarcode.extra_doc import canonical367 as m


@pytest.fixture(autouse=True)
def pure(monkeypatch):
    orig=m.map_journeys
    def checked(*a,**k):
        before=deepcopy((a,k))
        try:return orig(*a,**k)
        finally:assert (a,k)==before
    monkeypatch.setattr(m,'map_journeys',checked)


def exact(a,b):
    assert type(a) is type(b)
    if type(b) is dict:
        assert list(a)==list(b)
        for k in b:exact(a[k],b[k])
    elif type(b) in (list,tuple):
        assert len(a)==len(b)
        for x,y in zip(a,b):exact(x,y)
    elif type(b) is bool:assert a is b
    else:assert a==b


def det(a):
    result=F(0)
    for perm in permutations(range(len(a))):
        value=F((-1)**sum(perm[i]>perm[j] for i in range(len(a)) for j in range(i+1,len(a))))
        for i,j in enumerate(perm):value*=a[i][j]
        result+=value
    return result


def oracle(n,paths):
    pairs=[(a,b) for path in paths for a,b in zip(path,path[1:])]
    p=[tuple(F(pairs.count((i,j)),sum(a==i for a,b in pairs)) for j in range(n+2)) for i in range(n)]
    a=[[F(int(i==j))-p[i][j] for j in range(n)] for i in range(n)];den=det(a)
    def solve(rhs):
        out=[]
        for col in range(n):
            matrix=[row.copy() for row in a]
            for i in range(n):matrix[i][col]=rhs[i]
            out.append(det(matrix)/den)
        return out
    columns=[solve([int(i==j) for i in range(n)]) for j in range(n)]
    return dict(transition=p,visits=[tuple(columns[j][i] for j in range(n)) for i in range(n)],
                expected_steps=solve([1]*n),success_probability=solve([row[-1] for row in p]),journey_validated=False)


def test_cramer_absorption_oracle():
    rng=random.Random(367)
    for n in (1,2,3):
        for _ in range(90):
            paths=[(i,rng.choice((n,n+1))) for i in range(n)]
            while len(paths)<6 and rng.randrange(2):
                paths.append(tuple(rng.randrange(n) for _ in range(rng.randint(1,5)))+(rng.choice((n,n+1)),))
            rng.shuffle(paths);expected=oracle(n,paths);exact(m.map_journeys(n,paths),expected)
    exact(m.map_journeys(1,[(0,0,2),(0,1)]),dict(transition=[(F(1,3),F(1,3),F(1,3))],visits=[(F(3,2),)],
          expected_steps=[F(3,2)],success_probability=[F(1,2)],journey_validated=False))
    for n in (1,3):
        p=[tuple(range(n))+(n+1,)]*6;exact(m.map_journeys(n,p),oracle(n,p))
    paths=[(0,1,2,0,1,4)]*6;exact(m.map_journeys(3,paths),oracle(3,paths))


class I(int):pass
class L(list):pass
class T(tuple):pass


def fail(n,p,msg):
    with pytest.raises(ValueError) as e:m.map_journeys(n,p)
    assert str(e.value)==msg


def test_caps_types_first_bad():
    for x in (True,1.0,I(1),None,0,4):fail(x,None,'states must be exact int1..3')
    for x in (None,(),L([(0,1)]),[],[(0,1)]*7):fail(1,x,'journeys must be exact list1..6')
    for pos in range(6):
        for x in (None,[],T((0,1)),(),(0,),(0,)*7):
            p=[(0,3)]*6;p[pos]=x;fail(3,p,'journey must be exact tuple2..6')
        for col in range(6):
            for x in (True,1.0,I(1),None,-1,5):
                row=[0]*5+[3];row[col]=x;p=[(0,3)]*6;p[pos]=tuple(row);fail(3,p,'journey IDs must be exact declared ints')
    fail(1,[(1,0),None],'journey prefix must be transient')
    fail(1,[(0,0),None],'journey must end absorbing')
    fail(2,[(0,2)],'all transient states must appear')
    fail(1,[(0,True),None],'journey IDs must be exact declared ints')
    assert m.SCOPE=='PARTIAL: exact empirical absorbing touchpoint journey frequencies visits and completion'
    assert m.NOT_CLAIMED==('authentic customer behavior','Markov validity','causal influence','future conversion','business advice')
