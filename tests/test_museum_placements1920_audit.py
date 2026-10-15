import unittest,itertools as it,random,copy
from sugarcode.extra_doc import museum_placements1920 as m
import test_museum_placements1920 as builder
class L(list):pass
class T(tuple):pass
class D(dict):pass
class S(str):pass
class I(int):pass

def exact(a,b):
    assert type(a) is type(b),(a,b)
    if type(b) is dict:
        assert list(a)==list(b)
        for k in b:exact(a[k],b[k])
    elif type(b) in (list,tuple):
        assert len(a)==len(b)
        for x,y in zip(a,b):exact(x,y)
    else:assert a==b,(a,b)
def oracle(matrix):
    n=len(matrix);w=len(matrix[0])
    def count(rows,columns):
        if not rows:return 1
        if len(rows)>len(columns):return 0
        i=rows[0]
        return sum(count(rows[1:],columns-{j}) for j in columns if matrix[i][j])
    rows=list(range(n));columns=set(range(w));total=count(rows,columns)
    usage=[[count([r for r in rows if r!=i],columns-{j}) if matrix[i][j] else 0 for j in range(w)] for i in rows]
    return dict(placement_count=total,usage_counts=usage,curatorial_quality_validated=False)
def check(matrix):
    old=copy.deepcopy(matrix);r=m.placements(matrix);assert matrix==old;exact(r,oracle(matrix));assert all(sum(row)==r['placement_count'] for row in r['usage_counts']);r['usage_counts'].clear();exact(m.placements(matrix),oracle(matrix))
class Quick(unittest.TestCase):
    def test_valid(self):
        exact(m.SCOPE,'PARTIAL: supplied binary artifact-display injective placement counting');exact(m.NOT_CLAIMED,('curatorial quality','real artifact suitability','museum operations','production readiness'))
        for n in range(1,6):
            for w in range(1,7):
                check([[1]*w for _ in range(n)]);check([[0]*w for _ in range(n)]);check([[int(i==j) for j in range(w)] for i in range(n)])
        exact(m.placements([[1]*6 for _ in range(5)]),dict(placement_count=720,usage_counts=[[120]*6 for _ in range(5)],curatorial_quality_validated=False))
        rng=random.Random(911920)
        for _ in range(100):
            w=rng.randrange(1,7);check([[rng.randrange(2) for _ in range(w)] for _ in range(rng.randrange(1,6))])
    def test_validation(self):
        old=builder.m;builder.m=m
        try:builder.test_validation()
        finally:builder.m=old
        for value in ('\x1f','\x7f',' ','~',T(),L(),D(),S('1')):
            old=builder.m;builder.m=m
            try:builder.fail([[value]],'compatibility cell exact binary int')
            finally:builder.m=old
class Exhaustive(unittest.TestCase):
    def test_all_small(self):
        for n in range(1,4):
            for w in range(1,5):
                for bits in it.product(range(2),repeat=n*w):check([list(bits[i*w:(i+1)*w]) for i in range(n)])
    def test_random(self):
        rng=random.Random(601920)
        for _ in range(500):
            w=rng.randrange(1,7);check([[rng.randrange(2) for _ in range(w)] for _ in range(rng.randrange(1,6))])
