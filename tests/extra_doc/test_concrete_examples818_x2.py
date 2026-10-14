import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.concrete_examples818_x2 import interval_example_checks as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0, 0), ('b', 1, 2, 1)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^examples: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^examples: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'examples: row count outside declared range'),([None]*33,'examples: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'examples: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'example labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, -1000, 1000), (2, -1000, 1000), (3, -1000, 1000)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_independent_distance_oracle():
    for lo,hi,val in itertools.product((-1000,-1,0,1,1000),repeat=3):
        if lo>hi:
            with pytest.raises(ValueError,match='^lower must not exceed upper$'):run([('a',lo,hi,val)])
        else:
            inside=val in range(lo,hi+1);nearest=min((lo,hi),key=lambda p:abs(val-p))
            assert run([('a',lo,hi,val)])=={'inside':['a'] if inside else [],'corrections':[] if inside else [('a',nearest)],'understanding_evaluated':False}
    for val in (0,2):
        rows=[('e_'+str(i).zfill(2),0,1,val) for i in reversed(range(32))];r=run(rows)
        assert r['inside']==(sorted(x[0] for x in rows) if val==0 else [])
        assert r['corrections']==([] if val==0 else [(x[0],1) for x in sorted(rows)])
    from sugarcode.extra_doc import concrete_examples818_x2 as m
    assert 'NOT_CLAIMED: illustrative quality, conceptual understanding, abstraction,' in m.__doc__

def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^example labels must be unique$'):run([('a',0,0,0),('a',1,2,1)])
    assert run([('a',0,0,0),('b',0,0,0)])['inside']==['a','b']
