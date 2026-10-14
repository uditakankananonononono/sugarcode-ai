import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.causal_reasoning846_x2 import observed_group_differences as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 1, 0, 1), ('b', 1, 2, 1, 2)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^groups: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^groups: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'groups: row count outside declared range'),([None]*33,'groups: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'groups: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'group labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 100), (2, 1, 100), (3, 0, 100), (4, 1, 100)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^group labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_cross_product_oracle():
    for ts,tn,cs,cn in itertools.product((0,1,100),(1,2,100),(0,1,100),(1,2,100)):
        if ts>tn or cs>cn:
            with pytest.raises(ValueError,match='^successes must not exceed group totals$'):run([('a',ts,tn,cs,cn)])
        else:assert run([('a',ts,tn,cs,cn)])=={'differences':[('a',F(ts*cn-cs*tn,tn*cn))],'causality_identified':False}
    rows=[('g_'+str(i).zfill(2),1,2,1,3) for i in reversed(range(32))];assert run(rows)['differences']==[(r[0],F(1,6)) for r in sorted(rows)]
    from sugarcode.extra_doc import causal_reasoning846_x2 as m
    assert 'NOT_CLAIMED: causal identification, randomized assignment, valid controls,' in m.__doc__


def test_mixed_row_containers_and_label_charset():
    mixed=[tuple(ROWS[0]),list(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    mixed=[list(ROWS[0]),tuple(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    for bad in ('a-b','a.b','a b','a/b','a@b'):
        second=list(ROWS[1]);second[0]=bad
        with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],second])
