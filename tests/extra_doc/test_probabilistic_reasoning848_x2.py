import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.probabilistic_reasoning848_x2 import declared_weight_shares as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0), ('b', 1)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^weights: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^weights: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'weights: row count outside declared range'),([None]*33,'weights: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'weights: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'weight labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;r[1]=1;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 1000000)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^weight labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[1]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_scaled_shares_oracle():
    rng=random.Random(848)
    for _ in range(500):
        rows=[('w_'+str(i),rng.randint(1,1000000)) for i in range(rng.randint(1,32))];denominator=0
        for _,w in rows:denominator+=w
        result=run(rows);assert result=={'shares':[(l,F(1,denominator)*w) for l,w in sorted(rows)],'beliefs_verified':False} and sum(f for _,f in result['shares'])==1
    with pytest.raises(ValueError,match='^at least one weight must be positive$'):run([('a',0)])
    assert run([('a',0),('b',1)])['shares']==[('a',0),('b',1)]
    rows=[('w_'+str(i).zfill(2),1000000) for i in reversed(range(32))];assert run(rows)['shares']==[(r[0],F(1,32)) for r in sorted(rows)]
    from sugarcode.extra_doc import probabilistic_reasoning848_x2 as m
    assert 'NOT_CLAIMED: valid beliefs, Bayesian evidence, calibrated uncertainty,' in m.__doc__
    assert run([('a',1),('b',1)])['shares']==[('a',F(1,2)),('b',F(1,2))]


def test_mixed_row_containers_and_label_charset():
    mixed=[tuple(ROWS[0]),list(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    mixed=[list(ROWS[0]),tuple(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    for bad in ('a-b','a.b','a b','a/b','a@b'):
        second=list(ROWS[1]);second[0]=bad
        with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],second])
