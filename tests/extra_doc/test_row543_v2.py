import pytest
from sugarcode.extra_doc.ml_pipeline543 import fit_evaluate as run
class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass
ROWS = [('a', 0, 1, 1), ('b', 2, 5, 1), ('c', 1, 4, 0)]

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
    with pytest.raises(ValueError,match='^duplicate sample$'):run(ROWS+[ROWS[0]])


def test_nonfirst_wrong_arity_exact():
    with pytest.raises(ValueError,match='^wrong row arity$'):run([ROWS[0],ROWS[1][:-1]]+ROWS[2:])


def test_three_training_nonintegral_fit_and_two_evaluation_full_contract():
    assert run([('z',3,2,1),('a',0,0,1),('m',1,2,1),('b',2,1,0),('c',-1,-1,0)])=={
        'slope_fraction':'4/7','intercept_fraction':'4/7',
        'predictions':[('a','4/7'),('b','12/7'),('c','0'),('m','8/7'),('z','16/7')],
        'evaluation_mse_fraction':'37/49','training_count':3,'evaluation_count':2}


def test_nonadjacent_equal_training_features_refused():
    with pytest.raises(ValueError,match='^training feature variance must be positive$'):
        run([('a',2,0,1),('b',0,1,0),('c',2,5,1)])
