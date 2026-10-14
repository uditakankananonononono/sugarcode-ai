import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.elaborative_interrogation815_x2 import reason_annotation_gaps as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 2)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^questions: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^questions: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'questions: row count outside declared range'),([None]*33,'questions: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'questions: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'question labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 100), (2, 0, 100)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_independent_annotation_oracle():
    for count,minimum in itertools.product((0,1,2,100),repeat=2):
        shortage=minimum-count
        assert run([('a',count,minimum)])=={'gaps':[('a',shortage)] if shortage>0 else [],'satisfied':[] if shortage>0 else ['a'],'reason_total':count,'understanding_evaluated':False}
    rows=[('q_'+str(i).zfill(2),i,16) for i in reversed(range(32))];r=run(rows)
    assert r['gaps']==[('q_'+str(i).zfill(2),16-i) for i in range(16)] and r['satisfied']==['q_'+str(i).zfill(2) for i in range(16,32)] and r['reason_total']==496
    from sugarcode.extra_doc import elaborative_interrogation815_x2 as m
    assert 'NOT_CLAIMED: meaningful reasons, asking why, understanding, learning' in m.__doc__

def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^question labels must be unique$'):run([('a',0,0),('a',1,2)])
    assert run([('a',1,2),('b',1,2)])['gaps']==[('a',1),('b',1)]
