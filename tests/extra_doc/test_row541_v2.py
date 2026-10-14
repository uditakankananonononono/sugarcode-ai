import pytest
from sugarcode.extra_doc.lambda_architecture541 import merge_batch_stream as run
class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass
ROWS = [('a', 2, 7, 0), ('a', 2, 9, 1), ('b', 3, -2, 0)]

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
    with pytest.raises(ValueError,match='^duplicate key version source$'):run(ROWS+[ROWS[0]])


def test_nonfirst_wrong_arity_exact():
    with pytest.raises(ValueError,match='^wrong row arity$'):run([ROWS[0],ROWS[1][:-1]]+ROWS[2:])


def test_nonadjacent_newer_batch_beats_older_stream():
    assert run([('a',5,7,0),('b',0,1,1),('a',4,9,1)])=={
        'view':[('a',5,7,0),('b',0,1,1)],'input_count':3}


def test_nonadjacent_equal_version_stream_wins_even_if_first():
    assert run([('a',1000000,-1000000,1),('b',0,1000000,0),('a',1000000,1000000,0)])=={
        'view':[('a',1000000,-1000000,1),('b',0,1000000,0)],'input_count':3}
