import copy
import itertools
import pytest
from sugarcode.extra_doc.ml_pipeline543 import fit_evaluate as run

ROWS = [('a', 0, 1, 1), ('b', 2, 5, 1), ('c', 1, 4, 0)]
WANT = {'slope_fraction': '2', 'intercept_fraction': '1', 'predictions': [('a', '1'), ('b', '5'), ('c', '3')], 'evaluation_mse_fraction': '1', 'training_count': 2, 'evaluation_count': 1}


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


@pytest.mark.parametrize('slot,low,high', [(1, -1000, 1000), (2, -1000, 1000), (3, 0, 1)])
@pytest.mark.parametrize('bad', [None, True, False, 1.0, '1', [], {}])
def test_each_numeric_slot_strict_type(slot, low, high, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact nonbool integer required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(1, -1000, 1000), (2, -1000, 1000), (3, 0, 1)])
def test_each_numeric_slot_endpoints_and_caps(slot, low, high):
    for value in (low, high):
        row = list(ROWS[0]); row[slot] = value
        assert run([tuple(row), ROWS[1], ROWS[2], ('extra_train', -1, 0, 1)])
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
        assert run([tuple(row), ROWS[1], ROWS[2], ('extra_train', -1, 0, 1)])


def test_row_cap_accepted():
    rows = []
    for i in range(32):
        row = list(ROWS[0]); row[0] = 'person_'+str(i); rows.append(tuple(row))
    rows[1] = ('train_second', 2, 5, 1)
    rows[2] = ('evaluation', 1, 4, 0)
    assert run(rows)


def test_two_point_fit_independent_literal_oracle_and_no_evaluation_leak():
    for left,right in itertools.product((-3,0,4),repeat=2):
        from fractions import Fraction as F
        slope=F(right-left,2); intercept=F(left)
        rows=[('a',0,left,1),('b',2,right,1),('c',1,7,0)]
        result=run(rows)
        assert result['slope_fraction']==str(slope)
        assert result['intercept_fraction']==str(intercept)
        assert result['evaluation_mse_fraction']==str((intercept+slope-7)**2)
        changed=run(rows[:2]+[('c',1,-9,0)])
        assert changed['slope_fraction']==result['slope_fraction']
        assert changed['intercept_fraction']==result['intercept_fraction']


def test_missing_split_and_zero_variance_errors():
    for rows in [[('a',0,1,1)], [('a',0,1,1),('b',1,2,1)], [('a',0,1,0),('b',1,2,0)]]:
        with pytest.raises(ValueError,match='^at least two training and one evaluation samples required$'):run(rows)
    with pytest.raises(ValueError,match='^training feature variance must be positive$'):
        run([('a',1,0,1),('b',1,5,1),('c',0,3,0)])


def test_nonunit_feature_mean_and_multiple_evaluation_mse():
    rows=[('a',2,5,1),('b',4,9,1),('c',0,0,0),('d',3,10,0)]
    result=run(rows)
    assert result=={'slope_fraction':'2','intercept_fraction':'1',
                    'predictions':[('a','5'),('b','9'),('c','1'),('d','7')],
                    'evaluation_mse_fraction':'5','training_count':2,'evaluation_count':2}


def test_single_training_with_evaluation_refuses_split_before_variance():
    with pytest.raises(ValueError,match='^at least two training and one evaluation samples required$'):
        run([('train',2,5,1),('eval',3,7,0)])
