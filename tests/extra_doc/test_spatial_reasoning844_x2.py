import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.spatial_reasoning844_x2 import lattice_point_distances as raw_run
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
ROWS=[('a', 0, 0, 0, 0), ('b', 1, 2, 3, 4)]
def run(rows):return raw_run(rows)
@pytest.mark.parametrize('C',[L,T])
def test_container_subclasses(C):
    with pytest.raises(TypeError,match='^points: exact list or tuple required$'):run(C(ROWS))
    with pytest.raises(TypeError,match='^points: exact list or tuple row required$'):run([ROWS[0],C(ROWS[1])])
@pytest.mark.parametrize('bad,error,msg',[(S('b'),TypeError,'exact string label required'),('',ValueError,'label must be 1..24 ASCII word characters'),('x'*25,ValueError,'label must be 1..24 ASCII word characters'),('bad!',ValueError,'label must be 1..24 ASCII word characters'),('é',ValueError,'label must be 1..24 ASCII word characters')])
def test_label_slot(bad,error,msg):
    r=list(ROWS[1]);r[0]=bad
    with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])
def test_shapes_caps_unique_maxlabel_plain():
    for records,msg in [([], 'points: row count outside declared range'),([None]*33,'points: row count outside declared range'),
                       ([ROWS[0],ROWS[1][:-1]],'points: wrong row arity'),([ROWS[0],ROWS[1],ROWS[0]],'point labels must be unique')]:
        with pytest.raises(ValueError,match='^'+msg+'$'):run(records)
    r=list(ROWS[0]);r[0]='x'*24;assert run((r,))

@pytest.mark.parametrize('slot,lo,hi',[(1, -1000, 1000), (2, -1000, 1000), (3, -1000, 1000), (4, -1000, 1000)])
def test_integer_slots(slot,lo,hi):
    for bad,error,msg in [(I(1),TypeError,'exact nonbool integer required'),(True,TypeError,'exact nonbool integer required'),(lo-1,ValueError,'integer outside declared range'),(hi+1,ValueError,'integer outside declared range')]:
        r=list(ROWS[1]);r[slot]=bad
        with pytest.raises(error,match='^'+msg+'$'):run([ROWS[0],tuple(r)])


def test_identity_key_independent_fields():
    second=list(ROWS[1]);second[0]=ROWS[0][0]
    with pytest.raises(ValueError,match='^point labels must be unique$'):run([ROWS[0],tuple(second)])
    second=list(ROWS[0]);second[0]='different'
    assert run([ROWS[0],tuple(second)])


def test_independent_coordinate_oracle():
    for x1,y1,x2,y2 in itertools.product((-1000,-1,0,1,1000),repeat=4):
        dx=max(x1,x2)-min(x1,x2);dy=max(y1,y2)-min(y1,y2)
        assert run([('a',x1,y1,x2,y2)])=={'distances':[('a',dx+dy,dx*dx+dy*dy)],'locations_verified':False}
    rows=[('p_'+str(i).zfill(2),-1000,-1000,1000,1000) for i in reversed(range(32))];assert run(rows)['distances']==[(r[0],4000,8000000) for r in sorted(rows)]
    from sugarcode.extra_doc import spatial_reasoning844_x2 as m
    assert 'NOT_CLAIMED: spatial intelligence, actual distances, map interpretation,' in m.__doc__


def test_mixed_row_containers_and_label_charset():
    mixed=[tuple(ROWS[0]),list(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    mixed=[list(ROWS[0]),tuple(ROWS[1])]
    assert run(mixed)==run([tuple(r) for r in mixed])
    for bad in ('a-b','a.b','a b','a/b','a@b'):
        second=list(ROWS[1]);second[0]=bad
        with pytest.raises(ValueError,match='^label must be 1..24 ASCII word characters$'):run([ROWS[0],second])
