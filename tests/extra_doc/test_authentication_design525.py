import copy
import itertools
import pytest
from sugarcode.extra_doc.authentication_design525 import evaluate_authentication as run

ROWS = [('amy', 1, 0, 1), ('bob', 1, 0, 0)]
WANT = {'decisions': [('amy', False), ('bob', True)]}


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


@pytest.mark.parametrize('size', [0, 3, 5])
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


@pytest.mark.parametrize('slot,low,high', [(1, 0, 1), (2, 0, 1), (3, 0, 1)])
@pytest.mark.parametrize('bad', [None, True, False, 1.0, '1', [], {}])
def test_each_numeric_slot_strict_type(slot, low, high, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact nonbool integer required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(1, 0, 1), (2, 0, 1), (3, 0, 1)])
def test_each_numeric_slot_endpoints_and_caps(slot, low, high):
    for value in (low, high):
        row = list(ROWS[0]); row[slot] = value
        assert run([tuple(row)])
    for value in (low-1, high+1, 10**1000):
        row = list(ROWS[0]); row[slot] = value
        with pytest.raises(ValueError, match='^integer outside declared range$'):
            run([tuple(row)])


def test_duplicate_identity_refused():
    with pytest.raises(ValueError, match='^duplicate '):
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


def test_complete_authentication_truth_table():
    for primary,second,required in itertools.product((0,1),repeat=3):
        accepted = (primary,second,required) in {(1,0,0),(1,1,0),(1,1,1)}
        assert run([('subject',primary,second,required)])=={'decisions':[('subject',accepted)]}


class L525(list): pass
class T525(tuple): pass
class S525(str): pass
class I525(int): pass


@pytest.mark.parametrize('container', [L525, T525])
def test_subclass_outer_and_row_v3(container):
    with pytest.raises(TypeError, match='^exact list required$'):
        run(container(ROWS))
    with pytest.raises(TypeError, match='^exact tuple row required$'):
        run([ROWS[0], container(ROWS[1])])


def test_label_subclass_nonfirst_v3():
    with pytest.raises(TypeError, match='^exact string label required$'):
        run([ROWS[0], (S525('bob'), 1, 0, 0)])


@pytest.mark.parametrize('slot', [1, 2, 3])
def test_bit_subclass_nonfirst_v3(slot):
    row = list(ROWS[1]); row[slot] = I525(row[slot])
    with pytest.raises(TypeError, match='^exact nonbool integer required$'):
        run([ROWS[0], tuple(row)])


def test_duplicate_subject_full_message_v3():
    with pytest.raises(ValueError, match='^duplicate subject$'):
        run([ROWS[0], ROWS[0]])
