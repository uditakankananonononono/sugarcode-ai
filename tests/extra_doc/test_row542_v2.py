import pytest
from sugarcode.extra_doc.kappa_architecture542 import replay_stream as run
class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass
ROWS = [('a', 'x', 2, 7), ('b', 'y', 1, -3), ('c', 'x', 3, 2)]

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses_nonfirst(container):
    with pytest.raises(TypeError,match='^exact list required$'):run(container(ROWS))
    with pytest.raises(TypeError,match='^exact tuple row required$'):run([ROWS[0],container(ROWS[1])]+ROWS[2:])

@pytest.mark.parametrize('slot',[0, 1])
def test_label_subclasses_nonfirst(slot):
    rows=list(ROWS);record=list(rows[1]);record[slot]=S(record[slot]);rows[1]=tuple(record)
    with pytest.raises(TypeError,match='^exact string label required$'):run(rows)

@pytest.mark.parametrize('slot',[2, 3])
def test_integer_subclasses_nonfirst(slot):
    rows=list(ROWS);record=list(rows[1]);record[slot]=I(record[slot]);rows[1]=tuple(record)
    with pytest.raises(TypeError,match='^exact nonbool integer required$'):run(rows)


def test_nonadjacent_duplicate_full_message():
    with pytest.raises(ValueError,match='^duplicate event$'):run(ROWS+[ROWS[0]])


def test_nonfirst_wrong_arity_exact():
    with pytest.raises(ValueError,match='^wrong row arity$'):run([ROWS[0],ROWS[1][:-1]]+ROWS[2:])


def test_nonadjacent_duplicate_key_sequence_full_message():
    with pytest.raises(ValueError,match='^duplicate key sequence$'):
        run([('a','x',2,1),('b','y',1,2),('c','x',2,3)])


def test_reverse_input_and_cross_key_tie_full_trace():
    assert run([('c','x',1000000,-1000000),('b','y',0,1000000),('a','x',0,1000000)])=={
        'state':[('x',0),('y',1000000)],
        'trace':[('a','x',0,0,1000000),('b','y',0,0,1000000),('c','x',1000000,1000000,0)],'events':3}
