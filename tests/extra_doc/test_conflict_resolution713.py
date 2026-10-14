import copy
import itertools
import pytest
from sugarcode.extra_doc.conflict_resolution713 import find_common_interval as run

ROWS = [('a', 0, 7), ('b', 2, 9)]
WANT = {'feasible': True, 'common_interval': (2, 7), 'proposal_fraction': '9/2', 'gap': 0}


def test_hand_literal_and_no_mutation():
    before = copy.deepcopy(ROWS)
    assert run(ROWS) == WANT
    assert ROWS == before


def test_permutations_preserve_result():
    for order in itertools.permutations(ROWS):
        assert run(list(order)) == WANT


@pytest.mark.parametrize('bad', [None, (), {}, iter([]), 'x', True])
def test_outer_schema_refuses_exactly(bad):
    with pytest.raises(TypeError, match='^exact list required$'):
        run(bad)


@pytest.mark.parametrize('size', [0, 33])
def test_outer_size_refused_before_row_scan(size):
    with pytest.raises(ValueError, match='^row count must be 1..32$'):
        run([None] * size)


@pytest.mark.parametrize('bad', [None, [], {}, 'x', 1, True])
def test_tuple_row_schema_refuses_exactly(bad):
    with pytest.raises(TypeError, match='^exact tuple row required$'):
        run([bad])


@pytest.mark.parametrize('size', [0, 2, 4])
def test_row_arity_precedes_slots(size):
    with pytest.raises(ValueError, match='^wrong row arity$'):
        run([(None,) * size])


@pytest.mark.parametrize('slot', [0])
@pytest.mark.parametrize('bad', [None, 1, True, 1.0, b'a', [], {}])
def test_each_label_slot_exact_type(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact string label required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot', [0])
@pytest.mark.parametrize('bad', ['', 'A', 'a b', 'a'*25, 'a\n', 'é'])
def test_each_label_slot_shape_and_cap(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(ValueError, match='^label must be 1..24 lowercase identifier characters$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(1, -1000000, 1000000), (2, -1000000, 1000000)])
@pytest.mark.parametrize('bad', [None, True, False, 1.0, '1', [], {}])
def test_each_numeric_slot_strict_type(slot, low, high, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact nonbool integer required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(1, -1000000, 1000000), (2, -1000000, 1000000)])
def test_each_numeric_slot_endpoints_and_caps(slot, low, high):
    for value in (low, high):
        row = list(ROWS[0]); row[slot] = value
        row[3-slot]=value
        assert run([tuple(row)])
    for value in (low-1, high+1, 10**1000):
        row = list(ROWS[0]); row[slot] = value
        with pytest.raises(ValueError, match='^integer outside declared range$'):
            run([tuple(row)])


def test_duplicate_identity_refused():
    with pytest.raises(ValueError, match='^duplicate party$'):
        run([ROWS[0], ROWS[0]])


def test_label_length_endpoints():
    for label in ('a', 'a'*24):
        row = list(ROWS[0]); row[0] = label
        assert run([tuple(row)])


def test_row_cap_accepted():
    rows = []
    for i in range(32):
        row = list(ROWS[0]); row[0] = 'person_'+str(i); rows.append(tuple(row))
    assert run(rows)



def test_container_and_scalar_subclasses_refused():
    class L(list):pass
    class T(tuple):pass
    class I(int):pass
    class S(str):pass
    with pytest.raises(TypeError,match='^exact list required$'):run(L(ROWS))
    with pytest.raises(TypeError,match='^exact tuple row required$'):run([T(ROWS[0])])
    for slot,value in enumerate(ROWS[0]):
        row=list(ROWS[0]);row[slot]=S(value) if type(value) is str else I(value)
        message='exact string label required' if type(value) is str else 'exact nonbool integer required'
        with pytest.raises(TypeError,match='^'+message+'$'):run([tuple(row)])


def test_intersection_boundary_disjoint_negative_and_reversed():
    for rows,want in [([('a',0,2),('b',2,4)],{'feasible':True,'common_interval':(2,2),'proposal_fraction':'2','gap':0}),([('a',-9,-5),('b',-4,1)],{'feasible':False,'common_interval':None,'proposal_fraction':None,'gap':1}),([('a',-3,0),('b',-2,-1)],{'feasible':True,'common_interval':(-2,-1),'proposal_fraction':'-3/2','gap':0})]:
        assert run(rows)==want
    with pytest.raises(ValueError,match='^reversed acceptance interval$'):run([('a',2,1)])



@pytest.mark.parametrize('label',['1a','_a','9'])
def test_label_initial_character_at_every_label_slot(label):
    for slot,value in enumerate(ROWS[0]):
        if type(value) is str:
            row=list(ROWS[0]);row[slot]=label
            with pytest.raises(ValueError,match='^label must be 1..24 lowercase identifier characters$'):run([tuple(row)])
