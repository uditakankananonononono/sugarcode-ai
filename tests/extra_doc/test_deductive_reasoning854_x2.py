import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.deductive_reasoning854_x2 import declared_material_implications as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 1)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^statements: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^statements: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'statements: row count outside declared range'),([None]*33,'statements: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'statements: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'statement labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 1), (2, 0, 1)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^statement labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_truth_table():
    table={(0,0):True,(0,1):True,(1,0):False,(1,1):True}
    for flags in itertools.product(table,repeat=3):
        rows=[(l,*bits) for l,bits in zip(('c','a','b'),flags)]
        assert run(rows)=={'truths':[(l,table[p,c],table[p,c]) for l,p,c in sorted(rows)],'proofs_verified':False}
    rows=[('s_'+str(i).zfill(2),1,0) for i in reversed(range(32))];assert run(rows)['truths']==[(r[0],False,False) for r in sorted(rows)]
    from sugarcode.extra_doc import deductive_reasoning854_x2 as m
    assert 'NOT_CLAIMED: real proof validity, sound premises, semantic propositions,' in m.__doc__
