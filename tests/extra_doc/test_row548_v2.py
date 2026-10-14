import pytest
from sugarcode.extra_doc.recommendation548 import recommend_items as run
class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass
ROWS = [('a', 1, 2), ('b', -1, 2), ('c', 0, 1)]

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
    with pytest.raises(ValueError,match='^duplicate item$'):run(ROWS+[ROWS[0]])


def test_nonfirst_wrong_arity_exact():
    with pytest.raises(ValueError,match='^wrong row arity$'):run([ROWS[0],ROWS[1][:-1]]+ROWS[2:])


def test_signed_products_zero_and_identifier_tie_full_contract():
    assert run([('z',-1000,-1000),('a',1000,1000),('b',-1000,1000),('c',0,-1000),('d',-2,-3)])=={
        'recommendations':[('a',1000000),('z',1000000),('d',6),('c',0),('b',-1000000)]}
