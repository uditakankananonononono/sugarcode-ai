import pytest
from sugarcode.extra_doc.model_registry545 import index_versions as run
class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass
ROWS = [('a', 1, 'x', 1), ('b', 1, 'y', 0), ('a', 2, 'z', 0)]

@pytest.mark.parametrize('container',[L,T])
def test_container_subclasses_nonfirst(container):
    with pytest.raises(TypeError,match='^exact list required$'):run(container(ROWS))
    with pytest.raises(TypeError,match='^exact tuple row required$'):run([ROWS[0],container(ROWS[1])]+ROWS[2:])

@pytest.mark.parametrize('slot',[0, 2])
def test_label_subclasses_nonfirst(slot):
    rows=list(ROWS);record=list(rows[1]);record[slot]=S(record[slot]);rows[1]=tuple(record)
    with pytest.raises(TypeError,match='^exact string label required$'):run(rows)

@pytest.mark.parametrize('slot',[1, 3])
def test_integer_subclasses_nonfirst(slot):
    rows=list(ROWS);record=list(rows[1]);record[slot]=I(record[slot]);rows[1]=tuple(record)
    with pytest.raises(TypeError,match='^exact nonbool integer required$'):run(rows)


def test_nonadjacent_duplicate_full_message():
    with pytest.raises(ValueError,match='^duplicate model version$'):run(ROWS+[ROWS[0]])


def test_nonfirst_wrong_arity_exact():
    with pytest.raises(ValueError,match='^wrong row arity$'):run([ROWS[0],ROWS[1][:-1]]+ROWS[2:])


def test_nonadjacent_multiple_active_full_error():
    with pytest.raises(ValueError,match='^multiple active versions per model$'):
        run([('a',1,'x',1),('b',1,'y',0),('a',2,'z',1)])


def test_latest_distinct_from_active_and_full_output():
    assert run([('a',1000000,'z',0),('b',1,'y',0),('a',1,'x',1)])=={
        'versions':[('a',1,'x',1),('a',1000000,'z',0),('b',1,'y',0)],
        'latest':[('a',1000000),('b',1)],'active':[('a',1,'x')]}


def test_active_reverse_and_permuted_order_v3():
    import itertools
    rows=[('n',1,'art_n',1),('m',1,'art_m',1),('z',2,'art_z',0)]
    for order in itertools.permutations(rows):
        assert run(list(order))['active']==[('m',1,'art_m'),('n',1,'art_n')]


def test_many_active_reverse_order_v3():
    rows=[('model_'+str(i).zfill(2),1,'art_'+str(i).zfill(2),1) for i in reversed(range(24))]
    assert run(rows)['active']==[(model,version,artifact) for model,version,artifact,_ in sorted(rows)]
