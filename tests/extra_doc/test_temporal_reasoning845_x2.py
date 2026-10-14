import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.temporal_reasoning845_x2 import declared_interval_overlaps as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 1), ('b', 1, 2)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^intervals: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^intervals: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'intervals: row count outside declared range'),([None]*33,'intervals: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'intervals: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'interval labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 1000000), (2, 0, 1000000)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^interval labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_integer_set_intersection():
    intervals=[(a,b) for a in range(4) for b in range(a+1,5)]
    for (sa,ea),(sb,eb) in itertools.product(intervals,repeat=2):
        points=set(range(sa,ea))&set(range(sb,eb));expected=[('a','b',len(points))] if points else []
        assert run([('b',sb,eb),('a',sa,ea)])=={'overlaps':expected,'events_verified':False}
    for s,e in ((0,0),(1,0),(1000000,1000000)):
        with pytest.raises(ValueError,match='^start must precede end$'):run([('a',s,e)])
    rows=[('i_'+str(i).zfill(2),0,1000000) for i in reversed(range(32))];labels=sorted(r[0] for r in rows)
    assert run(rows)['overlaps']==[(a,b,1000000) for i,a in enumerate(labels) for b in labels[i+1:]]
    from sugarcode.extra_doc import temporal_reasoning845_x2 as m
    assert 'NOT_CLAIMED: actual event timing, calendar availability, causal time order,' in m.__doc__
