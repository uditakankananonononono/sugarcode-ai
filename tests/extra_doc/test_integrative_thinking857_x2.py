import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.integrative_thinking857_x2 import declared_maximin_order as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 2)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^options: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^options: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'options: row count outside declared range'),([None]*33,'options: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'options: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'option labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 100), (2, 0, 100)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^option labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_rank_buckets():
    rng=random.Random(857)
    for _ in range(500):
        rows=[('o_'+str(i),rng.randrange(101),rng.randrange(101)) for i in range(rng.randint(1,32))];buckets={}
        for l,a,b in rows:worst=sorted((a,b))[0];buckets.setdefault((worst,a+b),[]).append(l)
        expected=[]
        for key in sorted(buckets,reverse=True):expected+=sorted(buckets[key])
        assert run(rows)=={'order':expected,'integration_evaluated':False}
    assert run([('a',100,0),('b',1,1),('c',1,2)])['order']==['c','b','a']
    rows=[('o_'+str(i).zfill(2),100,100) for i in reversed(range(32))];assert run(rows)['order']==sorted(r[0] for r in rows)
    from sugarcode.extra_doc import integrative_thinking857_x2 as m
    assert 'NOT_CLAIMED: real integration, tension resolution, relevant objectives,' in m.__doc__


def test_mixed_row_containers_and_label_charset():
    mixed=[tuple(ROWS[0]),list(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    mixed=[list(ROWS[0]),tuple(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    for bad in ('a-b','a.b','a b','a/b','a@b'):
        second=list(ROWS[1]);second[0]=bad
        with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],second])
