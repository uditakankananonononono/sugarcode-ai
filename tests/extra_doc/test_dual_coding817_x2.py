import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.dual_coding817_x2 import modality_pair_counts as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 2)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^concepts: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^concepts: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'concepts: row count outside declared range'),([None]*33,'concepts: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'concepts: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'concept labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 100), (2, 0, 100)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_independent_cancellation_oracle():
    for v,w in itertools.product((0,1,2,100),repeat=2):
        vs=list(range(v));ws=list(range(w));paired=0
        while vs and ws:vs.pop();ws.pop();paired+=1
        assert run([('a',v,w)])=={'pairs':[('a',paired,len(vs),len(ws))],'missing_modality':['a'] if not v*w else [],'learning_evaluated':False}
    rows=[('c_'+str(i).zfill(2),0,1) for i in reversed(range(32))];result=run(rows)
    assert result['pairs']==[(r[0],0,0,1) for r in sorted(rows)] and result['missing_modality']==sorted(r[0] for r in rows)
    from sugarcode.extra_doc import dual_coding817_x2 as m
    assert 'NOT_CLAIMED: actual dual coding, linked meanings, learning improvement,' in m.__doc__

def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^concept labels must be unique$'):run([('a',0,0),('a',1,2)])
    assert len(run([('a',1,2),('b',1,2)])['pairs'])==2
