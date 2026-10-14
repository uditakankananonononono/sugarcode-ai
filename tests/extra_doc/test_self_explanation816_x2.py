import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.self_explanation816_x2 import arithmetic_step_checks as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0, 0, 0), ('b', 1, 2, 1, 3)]
def run(rows):return raw_run(rows)
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

@pytest.mark.parametrize('slot,lo,hi',[(1, -1000, 1000), (2, -1000, 1000), (3, 0, 2), (4, -1000000, 1000000)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_independent_arithmetic_oracle():
    import operator
    ops=(operator.add,operator.sub,operator.mul)
    for a,b,op in itertools.product((-1000,-1,0,1,1000),(-1000,-1,0,1,1000),(0,1,2)):
        value=ops[op](a,b)
        assert run([('a',a,b,op,value)])=={'correct':['a'],'corrections':[],'understanding_evaluated':False}
        wrong=value+1 if value<1000000 else value-1
        assert run([('a',a,b,op,wrong)])['corrections']==[('a',value)]
    for correct in (True,False):
        rows=[('s_'+str(i).zfill(2),1,2,0,3 if correct else 4) for i in reversed(range(32))];r=run(rows)
        assert r['correct']==(sorted(x[0] for x in rows) if correct else [])
        assert r['corrections']==([] if correct else [(x[0],3) for x in sorted(rows)])
    from sugarcode.extra_doc import self_explanation816_x2 as m
    assert 'NOT_CLAIMED: actual self-explanation, reasoning quality, understanding,' in m.__doc__

def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^step labels must be unique$'):run([('a',0,0,0,0),('a',1,2,1,3)])
    assert run([('a',1,2,0,3),('b',1,2,0,3)])['correct']==['a','b']
