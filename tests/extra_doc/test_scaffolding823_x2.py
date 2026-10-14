import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.scaffolding823_x2 import prerequisite_masks as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 2)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^stages: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^stages: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'stages: row count outside declared range'),([None]*33,'stages: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'stages: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'stage labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 255), (2, 0, 255)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_independent_bitset_oracle():
    for req,done in itertools.product(range(256),repeat=2):
        needed={i for i in range(8) if (req//2**i)%2};have={i for i in range(8) if (done//2**i)%2};missing=sum(2**i for i in needed-have)
        assert run([('a',req,done)])=={'missing':[('a',missing)],'eligible':['a'] if not missing else [],'mastery_verified':False}
    rows=[('s_'+str(i).zfill(2),255,255) for i in reversed(range(32))];r=run(rows);assert r['eligible']==sorted(x[0] for x in rows) and r['missing']==[(x[0],0) for x in sorted(rows)]
    from sugarcode.extra_doc import scaffolding823_x2 as m
    assert 'NOT_CLAIMED: teaching scaffolds, progressive learning, actual mastery,' in m.__doc__

def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^stage labels must be unique$'):run([('a',0,0),('a',1,2)])
    assert run([('a',1,1),('b',1,1)])['eligible']==['a','b']
