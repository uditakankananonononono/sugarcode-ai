import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.counterfactual_reasoning847_x2 import declared_linear_alternatives as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0, 0, 0), ('b', 1, 2, 3, 4)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^scenarios: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^scenarios: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'scenarios: row count outside declared range'),([None]*33,'scenarios: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'scenarios: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'scenario labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, -100, 100), (2, -100, 100), (3, -100, 100), (4, -100, 100)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^scenario labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_polynomial_oracle():
    for base,alt,slope,intercept in itertools.product((-100,-1,0,1,100),repeat=4):
        baseline=sum((slope*base,intercept));alternative=sum((slope*alt,intercept))
        assert run([('a',base,alt,slope,intercept)])=={'alternatives':[('a',baseline,alternative,alternative-baseline)],'counterfactuals_verified':False}
    rows=[('s_'+str(i).zfill(2),-100,100,100,100) for i in reversed(range(32))];assert run(rows)['alternatives']==[(r[0],-9900,10100,20000) for r in sorted(rows)]
    from sugarcode.extra_doc import counterfactual_reasoning847_x2 as m
    assert 'NOT_CLAIMED: real counterfactuals, causal structure, model truth, feasible' in m.__doc__


def test_mixed_row_containers_and_label_charset():
    mixed=[tuple(ROWS[0]),list(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    mixed=[list(ROWS[0]),tuple(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    for bad in ('a-b','a.b','a b','a/b','a@b'):
        second=list(ROWS[1]);second[0]=bad
        with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],second])


def test_validation_precedence_label_before_integer():
    row=list(ROWS[1]);row[0]='a-b';row[1]=True
    with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],row])
    row[0]=None;row[1]=1000001
    with pytest.raises(TypeError,match='^exact string label required$'):run([ROWS[0],row])

def test_all_row_shapes_before_content():
    row=list(ROWS[0]);row[0]='a-b'
    with pytest.raises(ValueError,match='^scenarios: wrong row arity$'):run([row,ROWS[1][:-1]])

def test_equal_alternative_and_zero_slope():
    assert run([('a',100,100,100,-100)])['alternatives']==[('a',9900,9900,0)]
    assert run([('a',-100,100,0,7)])['alternatives']==[('a',7,7,0)]


def test_integer_field_order_with_multiple_bad_values():
    for first in range(1,len(ROWS[1])-1):
        row=list(ROWS[1]);row[first]=True;row[first+1]=1000001
        with pytest.raises(TypeError,match='^exact nonbool integer required$'):run([ROWS[0],row])
        row=list(ROWS[1]);row[first]=1000001;row[first+1]=True
        with pytest.raises(ValueError,match='^integer outside declared range$'):run([ROWS[0],row])
