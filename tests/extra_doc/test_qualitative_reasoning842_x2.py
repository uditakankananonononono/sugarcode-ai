import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.qualitative_reasoning842_x2 import declared_direction_products as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, -1)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^directions: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^directions: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'directions: row count outside declared range'),([None]*33,'directions: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'directions: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'direction labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, -1, 1), (2, -1, 1)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^direction labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_sign_table():
    table={(-1,-1):1,(-1,0):0,(-1,1):-1,(0,-1):0,(0,0):0,(0,1):0,(1,-1):-1,(1,0):0,(1,1):1}
    for (a,b),p in table.items():
        assert run([('a',a,b)])=={'products':[('a',p)],'positive':['a'] if p==1 else [],'negative':['a'] if p==-1 else [],'zero':['a'] if not p else [],'interpretation_verified':False}
    for a,b in table:
        rows=[('d_'+str(i).zfill(2),a,b) for i in reversed(range(32))];r=run(rows);p=table[a,b];key={-1:'negative',0:'zero',1:'positive'}[p]
        assert r[key]==sorted(x[0] for x in rows) and r['products']==[(x[0],p) for x in sorted(rows)]
    from sugarcode.extra_doc import qualitative_reasoning842_x2 as m
    assert 'NOT_CLAIMED: qualitative world models, semantic directions, causal truth,' in m.__doc__
