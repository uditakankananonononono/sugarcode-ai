import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.progress_monitoring828_x2 import progress_reading_changes as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0), ('b', 1)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^readings: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^readings: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'readings: row count outside declared range'),([None]*33,'readings: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'readings: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'reading labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 100)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^reading labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_adjacent_pair_oracle():
    for values in itertools.product((0,1,50,100),repeat=3):
        rows=list(zip(('z','a','b'),values));changes=[(b[0],b[1]-a[1]) for a,b in zip(rows,rows[1:])]
        assert run(rows)=={'changes':changes,'drops':[b[0] for a,b in zip(rows,rows[1:]) if b[1]<a[1]],'progress_verified':False}
    assert run([('a',100)])['changes']==[]
    rows=[('r_'+str(i),i) for i in reversed(range(32))];assert run(rows)['drops']==[r[0] for r in rows[1:]]
    from sugarcode.extra_doc import progress_monitoring828_x2 as m
    assert 'NOT_CLAIMED: verified progress, advancement quality, monitoring integrations,' in m.__doc__
