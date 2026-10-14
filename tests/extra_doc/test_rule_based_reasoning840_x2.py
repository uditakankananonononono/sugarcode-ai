import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.rule_based_reasoning840_x2 import implication_closure as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 2)]
def run(rows):return raw_run(rows,[])
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^rules: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^rules: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'rules: row count outside declared range'),([None]*33,'rules: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'rules: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'rule labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 15), (2, 0, 15)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


@pytest.mark.parametrize('C',[L,T])
def test_fact_subclasses(C):
    with pytest.raises(TypeError,match='^facts: exact list or tuple required$'):raw_run(ROWS,C([0]))
@pytest.mark.parametrize('bad,error,msg',[(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(-1,ValueError,'integer outside declared range'),(16,ValueError,'integer outside declared range')])
def test_fact_slots(bad,error,msg):
    with pytest.raises(error,match='^'+msg+'$'):raw_run(ROWS,[0,bad])
def test_fact_bounds_and_independent_oracle():
    with pytest.raises(ValueError,match='^facts: at most16 entries$'):raw_run(ROWS,[0]*17)
    with pytest.raises(ValueError,match='^facts must be unique$'):raw_run(ROWS,[0,0])
    assert raw_run(ROWS,tuple(range(16)))['facts']==list(range(16))
    rng=random.Random(840)
    for _ in range(500):
        rows=[('r_'+str(i),rng.randrange(16),rng.randrange(16)) for i in range(rng.randint(1,32))];facts=rng.sample(range(16),rng.randrange(17));before=copy.deepcopy((rows,facts));matrix=[[False]*16 for _ in range(16)]
        for i in range(16):matrix[i][i]=True
        for _,a,b in rows:matrix[a][b]=True
        for k in range(16):
            for i in range(16):
                for j in range(16):matrix[i][j]=matrix[i][j] or (matrix[i][k] and matrix[k][j])
        expected=[j for j in range(16) if any(matrix[i][j] for i in facts)]
        assert raw_run(rows,facts)=={'facts':expected,'rules_verified':False} and (rows,facts)==before
    assert raw_run([('r_'+str(i),i,(i+1)%16) for i in reversed(range(16))],[0])['facts']==list(range(16))
    from sugarcode.extra_doc import rule_based_reasoning840_x2 as m
    assert 'NOT_CLAIMED: real-world inference, rule truth, sound knowledge, general' in m.__doc__
def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^rule labels must be unique$'):run([('a',0,0),('a',1,2)])
    assert raw_run([('a',1,2),('b',1,2)],[1])['facts']==[1,2]


def test_mixed_row_containers_and_label_charset():
    mixed=[tuple(ROWS[0]),list(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    mixed=[list(ROWS[0]),tuple(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    for bad in ('a-b','a.b','a b','a/b','a@b'):
        second=list(ROWS[1]);second[0]=bad
        with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],second])
