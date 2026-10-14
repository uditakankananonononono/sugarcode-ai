import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.systems_thinking858_x2 import declared_flow_balances as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0, 0), ('b', 1, 2, 3)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^flows: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^flows: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'flows: row count outside declared range'),([None]*33,'flows: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'flows: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'flow labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 15), (2, 0, 15), (3, 0, 1000)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^flow labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_flow_accumulation():
    rng=random.Random(858)
    for _ in range(500):
        rows=[('f_'+str(i),rng.randrange(16),rng.randrange(16),rng.randrange(1001)) for i in range(rng.randint(1,32))];ins={};outs={}
        for _,s,t,a in rows:ins.setdefault(s,0);ins[t]=ins.get(t,0)+a;outs.setdefault(t,0);outs[s]=outs.get(s,0)+a
        assert run(rows)=={'balances':[(n,ins[n],outs[n],ins[n]-outs[n]) for n in sorted(ins)],'system_verified':False}
    assert run([('a',1,8,0)])['balances']==[(1,0,0,0),(8,0,0,0)]
    assert run([('a',0,0,1000)])['balances']==[(0,1000,1000,0)]
    assert run([('f_'+str(i),0,15,1000) for i in range(32)])['balances']==[(0,0,32000,-32000),(15,32000,0,32000)]
    from sugarcode.extra_doc import systems_thinking858_x2 as m
    assert 'NOT_CLAIMED: actual system understanding, valid flows, causal structure,' in m.__doc__


def test_mixed_row_containers_and_label_charset():
    for mixed in ([tuple(ROWS[0]),list(ROWS[1])],[list(ROWS[0]),tuple(ROWS[1])]):
        assert run(mixed)==run([tuple(r) for r in mixed])
    for bad in ('a-b','a.b','a b','a/b','a@b'):
        second=list(ROWS[1]);second[0]=bad
        with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],second])
