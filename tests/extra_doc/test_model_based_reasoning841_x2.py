import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.model_based_reasoning841_x2 import declared_transition_trace as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 2)]
def run(rows):return raw_run(rows,0,32)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^transitions: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^transitions: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'transitions: row count outside declared range'),([None]*33,'transitions: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'transitions: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'transition labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 31), (2, 0, 31)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


@pytest.mark.parametrize('slot,lo,hi',[(0,0,31),(1,0,32)])
def test_parameters(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        args=[0,32];args[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):raw_run(ROWS,*args)
def test_transition_oracle():
    rng=random.Random(841)
    for _ in range(500):
        states=rng.sample(range(32),rng.randint(1,32));rows=[('t_'+str(s),s,rng.randrange(32)) for s in states];start=rng.randrange(32);steps=rng.randrange(33);trace=[start]
        for _ in range(steps):
            matches=[b for _,a,b in rows if a==trace[-1]]
            if not matches:break
            trace+=matches
        assert raw_run(rows,start,steps)=={'trace':trace,'model_verified':False}
    assert raw_run([('a',0,0)],0,32)['trace']==[0]*33
    assert raw_run([('a',0,1)],0,0)['trace']==[0]
    assert raw_run([('a',0,1)],31,32)['trace']==[31]
    with pytest.raises(ValueError,match='^transition states must be unique$'):run([('a',0,1),('b',0,2)])
    from sugarcode.extra_doc import model_based_reasoning841_x2 as m
    assert 'NOT_CLAIMED: valid real-world model, predictions, general reasoning,' in m.__doc__
def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^transition labels must be unique$'):run([('a',0,0),('a',1,2)])
    assert raw_run([('a',0,2),('b',1,2)],0,1)['trace']==[0,2]
