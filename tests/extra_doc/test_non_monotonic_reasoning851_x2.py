import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.non_monotonic_reasoning851_x2 import declared_fact_revisions as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, True), ('b', 1, False)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^events: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^events: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'events: row count outside declared range'),([None]*33,'events: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'events: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'event labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 15)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])

@pytest.mark.parametrize('slot',[2])
@pytest.mark.parametrize('bad',[I(1),1,0,None,'True'])
def test_bool_slots(slot,bad):
    r=list(ROWS[1]);r[slot]=bad
    with pytest.raises(TypeError,match='^revision flags must be exact bool$'):run([ROWS[0],tuple(r)])


def test_independent_latest_event_oracle():
    for bits in itertools.product((False,True),repeat=6):
        rows=[('e_'+str(i),i%3,b) for i,b in enumerate(bits)];latest={};counts=[]
        for l,f,b in rows:latest[f]=int(b);counts.append((l,sum(latest.values())))
        assert run(rows)=={'facts':sorted(f for f,b in latest.items() if b),'active_counts':counts,'beliefs_verified':False}
    rows=[('e_'+str(i),15-i%16,True) for i in range(32)];assert run(rows)['facts']==list(range(16))
    assert run([('z',1,True),('a',1,False)])['facts']==[] and run([('a',1,False),('z',1,True)])['facts']==[1]
    from sugarcode.extra_doc import non_monotonic_reasoning851_x2 as m
    assert 'NOT_CLAIMED: justified belief revision, evidence quality, logical consistency,' in m.__doc__
def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^event labels must be unique$'):run([('a',0,True),('a',1,False)])
    assert run([('a',1,True),('b',1,True)])['facts']==[1]
    assert run([('a',1,True),('b',8,True)])['facts']==[1,8]


def test_mixed_row_containers_and_label_charset():
    mixed=[tuple(ROWS[0]),list(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    mixed=[list(ROWS[0]),tuple(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    for bad in ('a-b','a.b','a b','a/b','a@b'):
        second=list(ROWS[1]);second[0]=bad
        with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],second])
