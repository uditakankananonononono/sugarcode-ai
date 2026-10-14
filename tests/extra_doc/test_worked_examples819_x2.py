import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.worked_examples819_x2 import running_total_trace as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 2)]
def run(rows):return raw_run(rows,0)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^steps: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^steps: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'steps: row count outside declared range'),([None]*33,'steps: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'steps: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'step labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, -1000, 1000), (2, -32000, 32000)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])

@pytest.mark.parametrize('bad,error,msg',[(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(-1001,ValueError,'integer outside declared range'),(1001,ValueError,'integer outside declared range')])
def test_parameter_slot(bad,error,msg):
    with pytest.raises(error,match='^'+msg+'$'):raw_run([ROWS[0]],bad)


def test_independent_prefix_oracle():
    rng=random.Random(819)
    for _ in range(500):
        initial=rng.randint(-1000,1000);rows=[('s_'+str(i),rng.randint(-1000,1000),rng.randint(-32000,32000)) for i in range(rng.randint(1,32))]
        totals=[initial+sum(r[1] for r in rows[:i+1]) for i in range(len(rows))];before=copy.deepcopy(rows)
        assert raw_run(rows,initial)=={'mismatches':[(r[0],t) for r,t in zip(rows,totals) if r[2]!=t],'final_total':totals[-1],'learning_evaluated':False} and rows==before
    assert raw_run([('z',2,3),('a',-1,2)],1)['mismatches']==[]
    assert raw_run([('a',-1,2),('z',2,3)],1)['mismatches']==[('a',0),('z',2)]
    for initial,delta in itertools.product((-1000,0,1000),repeat=2):
        assert raw_run([('a',delta,initial+delta)],initial)['mismatches']==[]
    assert raw_run([('s_'+str(i),1000,0) for i in range(32)],1000)['final_total']==33000
    from sugarcode.extra_doc import worked_examples819_x2 as m
    assert 'NOT_CLAIMED: actual solutions, pedagogical quality, explanation validity,' in m.__doc__

def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^step labels must be unique$'):run([('a',0,0),('a',1,2)])
    assert run([('a',1,1),('b',1,1)])['final_total']==2
