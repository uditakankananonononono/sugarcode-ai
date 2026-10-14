import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.inductive_reasoning853_x2 import declared_pooled_rates as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 1), ('b', 1, 2)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^samples: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^samples: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'samples: row count outside declared range'),([None]*33,'samples: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'samples: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'sample labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 100), (2, 1, 100)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^sample labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_weighted_rate():
    for s,a in itertools.product((0,1,100),(1,2,100)):
        if s>a:
            with pytest.raises(ValueError,match='^successes must not exceed attempts$'):run([('a',s,a)])
        else:assert run([('a',s,a)])=={'rates':[('a',F(s)/a)],'pooled':F(s)/a,'generalization_verified':False}
    rng=random.Random(853)
    for _ in range(500):
        rows=[]
        for i in range(rng.randint(1,32)):
            n=rng.randint(1,100);rows.append(('s_'+str(i),rng.randint(0,n),n))
        total=sum(a for _,_,a in rows);weighted=sum(F(s,a)*F(a,total) for _,s,a in rows)
        assert run(rows)['pooled']==weighted
    assert run([('a',1,1),('b',0,3)])['pooled']==F(1,4)
    rows=[('s_'+str(i).zfill(2),1,2) for i in reversed(range(32))];assert run(rows)['rates']==[(r[0],F(1,2)) for r in sorted(rows)]
    from sugarcode.extra_doc import inductive_reasoning853_x2 as m
    assert 'NOT_CLAIMED: valid generalization, representative samples, statistical' in m.__doc__


def test_mixed_row_containers_and_label_charset():
    mixed=[tuple(ROWS[0]),list(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    mixed=[list(ROWS[0]),tuple(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    for bad in ('a-b','a.b','a b','a/b','a@b'):
        second=list(ROWS[1]);second[0]=bad
        with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],second])
