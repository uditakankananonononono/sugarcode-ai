import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.goal_setting827_x2 import declared_goal_status as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 1, 0, 0), ('b', 2, 1, 1)]
def run(rows):return raw_run(rows,1000000)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^goals: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^goals: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'goals: row count outside declared range'),([None]*33,'goals: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'goals: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'goal labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 1, 100), (2, 0, 100), (3, 0, 1000000)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])

@pytest.mark.parametrize('bad,error,msg',[(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(-1,ValueError,'integer outside declared range'),(1000001,ValueError,'integer outside declared range')])
def test_parameter_slot(bad,error,msg):
    with pytest.raises(error,match='^'+msg+'$'):raw_run([ROWS[0]],bad)


def test_independent_status_oracle():
    for target,current,deadline,clock in itertools.product((1,2,100),(0,1,100),(0,1,1000000),(0,1,1000000)):
        unmet=target-current;expected={'met':[],'overdue':[],'pending':[],'progress_verified':False}
        if unmet<=0:expected['met']=['a']
        else:expected['overdue' if clock-deadline>0 else 'pending']=[('a',unmet)]
        assert raw_run([('a',target,current,deadline)],clock)==expected
    for current,deadline,key in ((1,0,'met'),(0,0,'overdue'),(0,1,'pending')):
        rows=[('g_'+str(i).zfill(2),1,current,deadline) for i in reversed(range(32))];result=raw_run(rows,1)
        assert result[key]==(sorted(r[0] for r in rows) if key=='met' else [(r[0],1) for r in sorted(rows)])
    from sugarcode.extra_doc import goal_setting827_x2 as m
    assert 'NOT_CLAIMED: useful goals, motivation, meaningful objectives, verified' in m.__doc__

def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^goal labels must be unique$'):run([('a',1,0,0),('a',2,1,1)])
    assert len(run([('a',1,0,0),('b',1,0,0)])['overdue'])==2
