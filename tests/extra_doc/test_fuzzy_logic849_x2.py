import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.fuzzy_logic849_x2 import declared_membership_algebra as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 2)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^memberships: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^memberships: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'memberships: row count outside declared range'),([None]*33,'memberships: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'memberships: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'membership labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 10000), (2, 0, 10000)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^membership labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_sorted_pair_oracle():
    for a,b in itertools.product((0,1,4999,5000,5001,9999,10000),repeat=2):
        low,high=sorted((a,b));excess=a+b-10000;clamped=excess if excess>0 else 0
        assert run([('a',a,b)])=={'memberships':[('a',low,high,10000-a,clamped)],'memberships_verified':False}
    rows=[('m_'+str(i).zfill(2),10000,10000) for i in reversed(range(32))];assert run(rows)['memberships']==[(r[0],10000,10000,0,10000) for r in sorted(rows)]
    from sugarcode.extra_doc import fuzzy_logic849_x2 as m
    assert 'NOT_CLAIMED: valid fuzzy sets, vague meaning interpretation, decisions,' in m.__doc__
