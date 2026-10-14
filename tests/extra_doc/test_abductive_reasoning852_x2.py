import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.abductive_reasoning852_x2 import declared_covering_hypotheses as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 2)]
def run(rows):return raw_run(rows,0)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^hypotheses: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^hypotheses: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'hypotheses: row count outside declared range'),([None]*33,'hypotheses: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'hypotheses: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'hypothesis labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 255), (2, 0, 100)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])

@pytest.mark.parametrize('bad,error,msg',[(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(-1,ValueError,'integer outside declared range'),(256,ValueError,'integer outside declared range')])
def test_parameter_slot(bad,error,msg):
    with pytest.raises(error,match='^'+msg+'$'):raw_run([ROWS[0]],bad)


def test_independent_mask_inclusion():
    for coverage,observed in itertools.product(range(256),repeat=2):
        needed={i for i in range(8) if observed//2**i%2};supplied={i for i in range(8) if coverage//2**i%2};expected=[('a',1)] if needed<=supplied else []
        assert raw_run([('a',coverage,1)],observed)=={'covering':expected,'explanations_verified':False}
    rows=[('h_'+str(i).zfill(2),255,100) for i in reversed(range(32))];assert raw_run(rows,255)['covering']==[(r[0],100) for r in sorted(rows)]
    assert run([('a',0,100),('b',0,0)])['covering']==[('b',0),('a',100)]
    from sugarcode.extra_doc import abductive_reasoning852_x2 as m
    assert 'NOT_CLAIMED: real explanations, causal validity, hypothesis truth, best' in m.__doc__
def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^hypothesis labels must be unique$'):run([('a',0,0),('a',1,2)])
    assert run([('a',1,2),('b',1,2)])['covering']==[('a',2),('b',2)]
