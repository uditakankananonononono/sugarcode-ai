import pytest
from sugarcode.extra_doc.model_monitoring546 import monitor_drift as run
class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass
ROWS = [('a', 0, 1, 1), ('b', 2, 0, 1), ('c', 0, 0, 0)]

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses_nonfirst(container):
    with pytest.raises(TypeError,match='^exact list required$'):run(container(ROWS))
    with pytest.raises(TypeError,match='^exact tuple row required$'):run([ROWS[0],container(ROWS[1])]+ROWS[2:])

@pytest.mark.parametrize('slot',[0])
def test_label_subclasses_nonfirst(slot):
    rows=list(ROWS);record=list(rows[1]);record[slot]=S(record[slot]);rows[1]=tuple(record)
    with pytest.raises(TypeError,match='^exact string label required$'):run(rows)

@pytest.mark.parametrize('slot',[1, 2, 3])
def test_integer_subclasses_nonfirst(slot):
    rows=list(ROWS);record=list(rows[1]);record[slot]=I(record[slot]);rows[1]=tuple(record)
    with pytest.raises(TypeError,match='^exact nonbool integer required$'):run(rows)


def test_nonadjacent_duplicate_full_message():
    with pytest.raises(ValueError,match='^duplicate metric$'):run(ROWS+[ROWS[0]])


def test_nonfirst_wrong_arity_exact():
    with pytest.raises(ValueError,match='^wrong row arity$'):run([ROWS[0],ROWS[1][:-1]]+ROWS[2:])


def test_strict_threshold_signed_absolute_extremes_full_contract():
    assert run([('z',1000000,-1000000,1000000),('a',5,3,2),('b',0,0,0),('c',-5,-2,2)])=={
        'metrics':[('a',-2,2,False),('b',0,0,False),('c',3,3,True),('z',-2000000,2000000,True)],
        'flagged':['c','z']}
