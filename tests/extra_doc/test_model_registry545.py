import copy
import itertools
import pytest
from sugarcode.extra_doc.model_registry545 import index_versions as run

ROWS = [('m', 1, 'old', 0), ('m', 2, 'new', 1), ('n', 3, 'other', 0)]
WANT = {'versions': [('m', 1, 'old', 0), ('m', 2, 'new', 1), ('n', 3, 'other', 0)], 'latest': [('m', 2), ('n', 3)], 'active': [('m', 2, 'new')]}


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


@pytest.mark.parametrize('slot', [0, 2])
@pytest.mark.parametrize('bad', [None, 1, True, 1.0, b'a', [], {}])
def test_each_label_slot_exact_type(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact string label required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot', [0, 2])
@pytest.mark.parametrize('bad', ['', 'A', 'a b', 'a'*25, 'a\n', 'é'])
def test_each_label_slot_shape_and_cap(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(ValueError, match='^label must be 1..24 lowercase identifier characters$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(1, 1, 1000000), (3, 0, 1)])
@pytest.mark.parametrize('bad', [None, True, False, 1.0, '1', [], {}])
def test_each_numeric_slot_strict_type(slot, low, high, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact nonbool integer required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(1, 1, 1000000), (3, 0, 1)])
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


def test_unique_version_ignores_artifact_and_active_and_live_slot():
    with pytest.raises(ValueError,match='^duplicate model version$'):run([('m',1,'a',0),('m',1,'b',1)])
    with pytest.raises(ValueError,match='^multiple active versions per model$'):run([('m',1,'a',1),('m',2,'b',1)])
    rows=[('m',9,'old',0),('m',2,'live',1),('other',1,'same',1)]
    result=run(rows)
    assert result['latest']==[('m',9),('other',1)]
    assert result['active']==[('m',2,'live'),('other',1,'same')]
    assert run([('m',2,'live',0)])['active']==[]
