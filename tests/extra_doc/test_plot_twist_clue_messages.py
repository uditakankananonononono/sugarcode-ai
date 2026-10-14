"""Row 265 plot_twist: pin the declared message for malformed clue entries and the check order.

Tests-only; green on the current source, red against the mutants listed in the delivery note.
"""
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.plot_twist import design_twist

PAIR_MSG = 'each clue must be a pair (a, b)'


@pytest.mark.parametrize('clue', [(1,), [1], {1, 2}, 'ab', (1, 2, 3), [], (), None, 5, {'a': 1, 'b': 2}, frozenset({1, 2}), b'ab'])
def test_malformed_clue_entry_raises_declared_type_error(clue):
    with pytest.raises(TypeError) as exc:
        design_twist(F(1, 2), [clue], F(1, 4), F(1, 4))
    assert str(exc.value) == PAIR_MSG
    assert type(exc.value) is TypeError


@pytest.mark.parametrize('pool', [[(1,)], [{1, 2}], ['ab'], ((1,),), ({1, 2},), ('ab',)])
def test_malformed_pool_in_list_or_tuple_container(pool):
    with pytest.raises(TypeError, match=r'^each clue must be a pair \(a, b\)$'):
        design_twist(F(1, 2), pool, F(1, 4), F(1, 4))


def test_clue_shape_is_checked_before_values_and_before_prior():
    # a bad prior and a bad value elsewhere must not mask the clue-shape error
    with pytest.raises(TypeError) as exc:
        design_twist(5, [(F(1, 2), F(1, 2)), (1,)], F(1, 4), F(1, 4))
    assert str(exc.value) == PAIR_MSG
    with pytest.raises(TypeError) as exc:
        design_twist(F(1, 2), [(2, 3), 'ab'], F(1, 4), F(1, 4))      # (2, 3) is out of range but comes first
    assert str(exc.value) == PAIR_MSG


def test_valid_pair_entries_of_both_container_types_still_work():
    r1 = design_twist(F(1, 2), [(F(1, 2), F(1, 4))], F(1, 4), F(1, 4))
    r2 = design_twist(F(1, 2), [[F(1, 2), F(1, 4)]], F(1, 4), F(1, 4))
    assert r1 == r2
    # prior 1/2, one clue a=1/2 b=1/4: bayes factor 2, posterior (1/4)/(1/4+1/8) = 2/3
    assert r1['bayes_factor'] == 2 and r1['posterior'] == F(2, 3) and r1['surprise'] == F(1, 2)
