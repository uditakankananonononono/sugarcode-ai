import copy
import itertools
import pytest
from sugarcode.extra_doc.organizational_design479 import structure_teams as run

ROWS = [('amy', 'ops', 'sales'), ('bob', 'ops', 'support'), ('cam', 'build', 'dev')]
WANT = {'teams': [{'team': 'build', 'members': [('cam', 'dev')], 'functions': ['dev'], 'size': 1, 'cross_functional': False}, {'team': 'ops', 'members': [('amy', 'sales'), ('bob', 'support')], 'functions': ['sales', 'support'], 'size': 2, 'cross_functional': True}], 'people': 3, 'team_count': 2}


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


@pytest.mark.parametrize('slot', [0, 1, 2])
@pytest.mark.parametrize('bad', [None, 1, True, 1.0, b'a', [], {}])
def test_each_label_slot_exact_type(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact string label required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot', [0, 1, 2])
@pytest.mark.parametrize('bad', ['', 'A', 'a b', 'a'*25, 'a\n', 'é'])
def test_each_label_slot_shape_and_cap(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(ValueError, match='^label must be 1..24 lowercase identifier characters$'):
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


def test_group_membership_independent_oracle_and_perturbation():
    rows = [('p_'+str(i), 'team_'+str(i%3), 'fn_'+str(i%2)) for i in range(32)]
    result = run(rows)
    flat = [(person, group['team'], function) for group in result['teams'] for person,function in group['members']]
    assert sorted(flat) == sorted(rows)
    assert result['team_count'] == 3 and result['people'] == 32
    for group in result['teams']:
        expected = [x for x in rows if x[1] == group['team']]
        assert group['size'] == len(expected)
        assert group['functions'] == sorted(set(x[2] for x in expected))
        assert group['cross_functional'] == (len(set(x[2] for x in expected)) >= 2)
    assert run([('amy','ops','sales'),('bob','ops','sales')])['teams'][0]['cross_functional'] is False
    assert run([('amy','ops','sales'),('bob','ops','support')])['teams'][0]['cross_functional'] is True
