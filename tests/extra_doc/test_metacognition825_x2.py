import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.metacognition825_x2 import declared_prediction_errors as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 1)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^predictions: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^predictions: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'predictions: row count outside declared range'),([None]*33,'predictions: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'predictions: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'prediction labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 10000), (2, 0, 1)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_independent_scaled_integer_oracle():
    rng=random.Random(825)
    for _ in range(500):
        rows=[('p_'+str(i),rng.randrange(10001),rng.randrange(2)) for i in range(rng.randint(1,32))];scaled=[(l,c-10000*o) for l,c,o in rows]
        assert run(rows)=={'errors':[(l,F(v,10000)) for l,v in sorted(scaled)],'brier':F(sum(v**2 for _,v in scaled),len(rows)*100000000),'metacognition_evaluated':False}
    for c,o in itertools.product((0,1,5000,9999,10000),(0,1)):
        assert run([('a',c,o)])['brier']==F((c-10000*o)**2,100000000)
    rows=[('p_'+str(i).zfill(2),0,0) for i in reversed(range(32))];assert run(rows)['errors']==[(r[0],0) for r in sorted(rows)]
    from sugarcode.extra_doc import metacognition825_x2 as m
    assert 'NOT_CLAIMED: actual metacognition, thinking quality, valid observations,' in m.__doc__

def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^prediction labels must be unique$'):run([('a',0,0),('a',1,1)])
    assert len(run([('a',1,1),('b',1,1)])['errors'])==2


def test_mixed_row_containers_and_label_charset():
    mixed=[tuple(ROWS[0]),list(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    mixed=[list(ROWS[0]),tuple(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    for bad in ('a-b','a.b','a b','a/b','a@b'):
        second=list(ROWS[1]);second[0]=bad
        with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],second])
