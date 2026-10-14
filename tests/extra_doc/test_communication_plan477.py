import copy
import itertools
import pytest
from sugarcode.extra_doc.communication_plan477 import plan_messages as run

ROWS = [('staff', 'email', 'launch', 'lead', 2), ('buyers', 'web', 'price', 'sales', 0)]
WANT = {'matrix': [('buyers', 'web', 'price', 'sales', 0), ('staff', 'email', 'launch', 'lead', 2)], 'audiences': ['buyers', 'staff'], 'channels': ['email', 'web'], 'message_count': 2}


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


@pytest.mark.parametrize('size', [0, 4, 6])
def test_row_arity_precedes_slots(size):
    with pytest.raises(ValueError, match='^wrong row arity$'):
        run([(None,) * size])


@pytest.mark.parametrize('slot', [0, 1, 2, 3])
@pytest.mark.parametrize('bad', [None, 1, True, 1.0, b'a', [], {}])
def test_each_label_slot_exact_type(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact string label required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot', [0, 1, 2, 3])
@pytest.mark.parametrize('bad', ['', 'A', 'a b', 'a'*25, 'a\n', 'é'])
def test_each_label_slot_shape_and_cap(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(ValueError, match='^label must be 1..24 lowercase identifier characters$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(4, 0, 365)])
@pytest.mark.parametrize('bad', [None, True, False, 1.0, '1', [], {}])
def test_each_numeric_slot_strict_type(slot, low, high, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact nonbool integer required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(4, 0, 365)])
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


def test_perturbation_and_independent_matrix_oracle():
    rows = [('group_'+str(i%4), 'mail', 'fact_'+str(i), 'owner', (31-i)%7) for i in range(32)]
    result = run(rows)
    assert result['matrix'] == sorted(rows, key=lambda x: (x[-1], *x[:-1]))
    assert result['message_count'] == 32
    for slot, value in enumerate(('newgroup', 'newchannel', 'newfact', 'newowner', 365)):
        changed = list(rows[0]); changed[slot] = value
        assert run([tuple(changed)])['matrix'] != run([rows[0]])['matrix']


@pytest.mark.parametrize('slot', range(4))
def test_day_ties_resolve_by_every_declared_label_slot(slot):
    lower = ['a','x','f','o',1]
    upper = lower.copy()
    upper[slot] = {'a':'b','x':'y','f':'g','o':'p'}[lower[slot]]
    expected = [tuple(lower),tuple(upper)]
    for supplied in (expected, list(reversed(expected))):
        assert run(supplied)['matrix'] == expected
