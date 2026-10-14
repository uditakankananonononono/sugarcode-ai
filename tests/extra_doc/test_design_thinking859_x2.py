import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.design_thinking859_x2 import declared_prototype_screen as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0), ('b', 1, 2)]
def run(rows):return raw_run(rows,0)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^prototypes: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^prototypes: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'prototypes: row count outside declared range'),([None]*33,'prototypes: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'prototypes: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'prototype labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, 0, 255), (2, 0, 1000)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])

@pytest.mark.parametrize('bad,error,msg',[(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(-1,ValueError,'integer outside declared range'),(256,ValueError,'integer outside declared range')])
def test_parameter_slot(bad,error,msg):
    with pytest.raises(error,match='^'+msg+'$'):raw_run([ROWS[0]],bad)


def test_independent_bitset_screen():
    rng=random.Random(859)
    for _ in range(500):
        rows=[('p_'+str(i),rng.randrange(256),rng.randrange(1001)) for i in range(rng.randint(1,32))];req=rng.randrange(256);needed={i for i in range(8) if req//2**i%2};selected=[]
        for l,c,e in rows:
            covered={i for i in range(8) if c//2**i%2}
            if needed<=covered:selected.append((len(covered-needed),e,l))
        assert raw_run(rows,req)=={'prototypes':[(l,n,e) for n,e,l in sorted(selected)],'designs_validated':False}
    assert raw_run([('a',3,0),('b',1,1000),('c',1,0)],1)['prototypes']==[('c',0,0),('b',0,1000),('a',1,0)]
    rows=[('p_'+str(i).zfill(2),255,1000) for i in reversed(range(32))];assert raw_run(rows,255)['prototypes']==[(r[0],0,1000) for r in sorted(rows)]
    from sugarcode.extra_doc import design_thinking859_x2 as m
    assert 'NOT_CLAIMED: useful designs, validated needs, user research, creativity,' in m.__doc__
def test_identity_key_independent_fields():
    with pytest.raises(ValueError,match='^prototype labels must be unique$'):run([('a',0,0),('a',1,2)])
    assert len(run([('a',1,2),('b',1,2)])['prototypes'])==2


def test_mixed_row_containers_and_label_charset():
    for mixed in ([tuple(ROWS[0]),list(ROWS[1])],[list(ROWS[0]),tuple(ROWS[1])]):
        assert run(mixed)==run([tuple(r) for r in mixed])
    for bad in ('a-b','a.b','a b','a/b','a@b'):
        second=list(ROWS[1]);second[0]=bad
        with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],second])
