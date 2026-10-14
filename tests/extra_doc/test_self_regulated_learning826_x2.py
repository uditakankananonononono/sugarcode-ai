import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.self_regulated_learning826_x2 import declared_study_variances as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 1, 0), ('b', 2, 1)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^study: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^study: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'study: row count outside declared range'),([None]*33,'study: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'study: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'study labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 1, 1440), (2, 0, 1440)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_independent_aggregate_oracle():
    rng=random.Random(826)
    for _ in range(500):
        rows=[('s_'+str(i),rng.randint(1,1440),rng.randint(0,1440)) for i in range(rng.randint(1,32))];p=0;a=0;variances={}
        for l,plan,actual in rows:p+=plan;a+=actual;variances[l]=-(plan-actual)
        assert run(rows)=={'variances':sorted(variances.items()),'actual_to_plan':F(a,p),'learning_evaluated':False}
    for p,a in itertools.product((1,2,1440),(0,1,1440)):
        assert run([('a',p,a)])['actual_to_plan']==F(a,p)
    assert run([('a',1,1),('b',3,1)])['actual_to_plan']==F(1,2)
    rows=[('s_'+str(i).zfill(2),1,0) for i in reversed(range(32))];assert run(rows)['variances']==[(r[0],-1) for r in sorted(rows)]
    from sugarcode.extra_doc import self_regulated_learning826_x2 as m
    assert 'NOT_CLAIMED: actual self-regulation, study effectiveness, verified effort,' in m.__doc__

def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^study labels must be unique$'):run([('a',1,0),('a',2,1)])
    assert len(run([('a',1,1),('b',1,1)])['variances'])==2
