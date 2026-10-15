import copy,itertools,random,pytest
from sugarcode.extra_doc import museum_placements1920 as m
class L(list):pass
class I(int):pass

def oracle(matrix):
    n=len(matrix);w=len(matrix[0]);usage=[[0]*w for _ in matrix];count=0
    for assignment in itertools.permutations(range(w),n):
        if all(matrix[i][j] for i,j in enumerate(assignment)):
            count+=1
            for i,j in enumerate(assignment):usage[i][j]+=1
    return dict(placement_count=count,usage_counts=usage,curatorial_quality_validated=False)

def check(matrix):
    old=copy.deepcopy(matrix);out=m.placements(matrix);assert out==oracle(matrix)
    assert type(out) is dict and list(out)==['placement_count','usage_counts','curatorial_quality_validated']
    assert type(out['placement_count']) is int and type(out['usage_counts']) is list
    assert all(type(r) is list and all(type(x) is int for x in r) for r in out['usage_counts'])
    assert out['curatorial_quality_validated'] is False and matrix==old

def test_permutations():
    for n in range(1,4):
        for w in range(1,4):
            for cells in itertools.product(range(2),repeat=n*w):check([list(cells[i*w:(i+1)*w]) for i in range(n)])
    rng=random.Random(1920)
    for _ in range(1000):
        w=rng.randint(1,6);check([[rng.randrange(2) for _ in range(w)] for _ in range(rng.randint(1,5))])
    check([[1]*6 for _ in range(5)]);check([[0]*6 for _ in range(5)])
    assert m.SCOPE=='PARTIAL: supplied binary artifact-display injective placement counting'
    assert m.NOT_CLAIMED==('curatorial quality','real artifact suitability','museum operations','production readiness')

def fail(matrix,msg):
    old=copy.deepcopy(matrix)
    with pytest.raises(ValueError) as e:m.placements(matrix)
    assert str(e.value)==msg and matrix==old

def test_validation():
    for x in (None,(),L([[0]]),[],[[0]]*6):fail(x,'compatibility exact list1..5')
    for x in (None,(),L([0]),[],[0]*7):fail([x],'first compatibility row exact list1..6')
    for x in (None,(),L([0]),[],[0,0]):fail([[0],x],'compatibility row exact list matching width')
    for i in range(5):
        for j in range(6):
            for x in (-1,2,True,I(0),0.0,None,'x'):
                matrix=[[0]*6 for _ in range(5)];matrix[i][j]=x;fail(matrix,'compatibility cell exact binary int')
    fail([[None],None],'compatibility cell exact binary int')
