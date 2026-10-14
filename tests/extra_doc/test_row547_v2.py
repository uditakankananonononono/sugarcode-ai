import pytest
from sugarcode.extra_doc.ab_infrastructure547 import summarize_experiment as run
class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass
ROWS = [('a', 0, 1), ('b', 1, 0), ('c', 0, 0)]

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses_nonfirst(container):
    with pytest.raises(TypeError,match='^exact list required$'):run(container(ROWS))
    with pytest.raises(TypeError,match='^exact tuple row required$'):run([ROWS[0],container(ROWS[1])]+ROWS[2:])

@pytest.mark.parametrize('slot',[0])
def test_label_subclasses_nonfirst(slot):
    rows=list(ROWS);record=list(rows[1]);record[slot]=S(record[slot]);rows[1]=tuple(record)
    with pytest.raises(TypeError,match='^exact string label required$'):run(rows)

@pytest.mark.parametrize('slot',[1, 2])
def test_integer_subclasses_nonfirst(slot):
    rows=list(ROWS);record=list(rows[1]);record[slot]=I(record[slot]);rows[1]=tuple(record)
    with pytest.raises(TypeError,match='^exact nonbool integer required$'):run(rows)


def test_nonadjacent_duplicate_full_message():
    with pytest.raises(ValueError,match='^duplicate unit$'):run(ROWS+[ROWS[0]])


def test_nonfirst_wrong_arity_exact():
    with pytest.raises(ValueError,match='^wrong row arity$'):run([ROWS[0],ROWS[1][:-1]]+ROWS[2:])


def test_single_arm_full_error():
    for rows in [[('a',0,1),('b',0,0)],[('a',1,1),('b',1,0)]]:
        with pytest.raises(ValueError,match='^both experiment arms required$'):run(rows)


def test_unequal_arm_sizes_exact_negative_difference_full_contract():
    assert run([('a',0,1),('b',1,1),('c',0,0),('d',1,0),('e',1,0)])=={
        'arms':[(0,2,1,'1/2'),(1,3,1,'1/3')],'difference_fraction':'-1/6'}
