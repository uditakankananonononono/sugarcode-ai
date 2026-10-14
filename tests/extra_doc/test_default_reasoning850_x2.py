import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.default_reasoning850_x2 import declared_default_bits as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', True, False), ('b', False, True)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^defaults: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^defaults: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'defaults: row count outside declared range'),([None]*33,'defaults: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'defaults: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'default labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot',[1, 2])
@pytest.mark.parametrize('bad',[I(1),1,0,None,'True'])
def test_bool_slots(slot,bad):
    r=list(ROWS[1]);r[slot]=bad
    with pytest.raises(TypeError,match='^default flags must be exact bool$'):run([ROWS[0],tuple(r)])


def test_independent_default_truth_table():
    table={(False,False):'inactive',(False,True):'inactive',(True,False):'accepted',(True,True):'blocked'}
    for flags in itertools.product(table,repeat=3):
        rows=[(l,*bits) for l,bits in zip(('c','a','b'),flags)];buckets={'accepted':[],'blocked':[],'inactive':[],'assumptions_verified':False}
        for l,d,c in sorted(rows):buckets[table[d,c]].append(l)
        assert run(rows)==buckets
    for d,c in table:
        rows=[('d_'+str(i).zfill(2),d,c) for i in reversed(range(32))];assert run(rows)[table[d,c]]==sorted(r[0] for r in rows)
    from sugarcode.extra_doc import default_reasoning850_x2 as m
    assert 'NOT_CLAIMED: defensible assumptions, knowledge truth, contradiction detection,' in m.__doc__
def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^default labels must be unique$'):run([('a',True,False),('a',False,True)])
    assert run([('a',True,False),('b',True,False)])['accepted']==['a','b']
