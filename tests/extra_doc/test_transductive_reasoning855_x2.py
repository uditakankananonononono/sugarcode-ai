import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.transductive_reasoning855_x2 import nearest_declared_exemplars as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 1)]
def run(rows):return raw_run(rows,0)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^exemplars: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^exemplars: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'exemplars: row count outside declared range'),([None]*33,'exemplars: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'exemplars: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'exemplar labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, -1000, 1000), (2, 0, 15)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])

@pytest.mark.parametrize('bad,error,msg',[(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(-1001,ValueError,'integer outside declared range'),(1001,ValueError,'integer outside declared range')])
def test_parameter_slot(bad,error,msg):
    with pytest.raises(error,match='^'+msg+'$'):raw_run([ROWS[0]],bad)


def test_independent_squared_distance_oracle():
    rng=random.Random(855)
    for _ in range(500):
        rows=[('e_'+str(i),rng.randint(-1000,1000),rng.randrange(16)) for i in range(rng.randint(1,32))];query=rng.randint(-1000,1000);squares=[((x-query)**2,l,c) for l,x,c in rows];minimum=min(s for s,_,_ in squares);selected=[(l,c) for s,l,c in squares if s==minimum]
        assert raw_run(rows,query)=={'distance':int(minimum**0.5),'exemplars':sorted(l for l,_ in selected),'class_codes':sorted(set(c for _,c in selected)),'classification_verified':False}
    assert raw_run([('a',-1,1),('b',1,8)],0)['class_codes']==[1,8]
    rows=[('e_'+str(i).zfill(2),1000,15-i%16) for i in reversed(range(32))];r=raw_run(rows,-1000)
    assert r['distance']==2000 and r['class_codes']==list(range(16)) and r['exemplars']==sorted(l for l,_,_ in rows)
    from sugarcode.extra_doc import transductive_reasoning855_x2 as m
    assert 'NOT_CLAIMED: valid classification, generalization, meaningful distance,' in m.__doc__
def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^exemplar labels must be unique$'):run([('a',0,0),('a',1,1)])
    assert run([('a',1,1),('b',1,1)])['exemplars']==['a','b']
