from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.design_sprint import plan_sprint as solve, NOT_CLAIMED


def oracle(rows, capacity):
    """Independent: bitmask enumeration, lexicographic key (-value, hours, size, indices)."""
    best = None
    for mask in range(1 << len(rows)):
        pick = [i for i in range(len(rows)) if mask >> i & 1]
        h = sum(F(rows[i][2]) for i in pick)
        if h > capacity:
            continue
        key = (-sum(F(rows[i][1]) for i in pick), h, len(pick), tuple(pick))
        if best is None or key < best:
            best = key
    return best


def test_hand_derived_literals():
    # capacity 2 days * 4 h = 8. (value/hours) a 6/5, b 5/4, c 4/3, d 1/1.
    # feasible pairs: a+c = 8h value 10 ; b+c = 7h value 9 ; a+d = 6h value 7 ; b+d = 5h value 6 ; a+b = 9h over ; triples all over
    r = solve([('a', 6, 5), ('b', 5, 4), ('c', 4, 3), ('d', 1, 1)], 4, 2)
    assert r['chosen'] == ['a', 'c'] and r['chosen_indices'] == [0, 2] and r['total_value'] == 10
    assert r['total_hours'] == 8 and r['capacity_hours'] == 8 and r['spare_hours'] == 0 and r['deferred'] == ['b', 'd']
    assert type(r['total_value']) is F


def test_default_days_is_five_and_capacity_boundary_inclusive():
    r = solve([('a', 3, 10)], 2)
    assert r['capacity_hours'] == 10 and r['chosen'] == ['a']                     # exactly fits
    assert solve([('a', 3, 11)], 2)['chosen'] == [] and solve([('a', 3, 11)], 2)['total_value'] == 0


def test_ties_fewer_hours_then_fewer_features_then_lexicographic():
    r = solve([('a', 5, 3), ('b', 5, 2)], 1, 1)                                   # capacity 1: nothing fits
    assert r['chosen'] == []
    r = solve([('a', 5, 3), ('b', 5, 2)], 3, 1)                                   # only one fits? 3h fits a; b 2h fits; both 5h no
    assert r['chosen'] == ['b']                                                   # same value 5, fewer hours
    r = solve([('a', 5, 2), ('b', 3, 1), ('c', 2, 1)], 2, 1)                      # b+c value 5 hours 2 vs a value 5 hours 2: fewer features
    assert r['chosen'] == ['a']
    r = solve([('a', 4, 2), ('b', 4, 2)], 2, 1)                                   # identical -> first
    assert r['chosen'] == ['a']
    r = solve([('a', 0, 0), ('b', 0, 0)], 1, 1)                                   # zero everything -> empty set
    assert r['chosen'] == [] and r['total_hours'] == 0


@pytest.mark.parametrize('rows,per_day,days', [
    ([('a', 6, 5), ('b', 5, 4), ('c', 4, 3), ('d', 1, 1), ('e', F(7, 2), F(5, 2))], 3, 3),
    ([('f%d' % k, 1 + (k * 7) % 5, 1 + (k * 3) % 4) for k in range(12)], 4, 4),
    ([('a', F(1, 3), F(1, 2)), ('b', F(1, 6), F(1, 4)), ('c', F(1, 2), F(3, 4))], F(1, 2), 2),
    ([('a', 2, 2), ('b', 2, 2), ('c', 2, 2)], 2, 2),
])
def test_matches_independent_oracle(rows, per_day, days):
    key = oracle(rows, F(per_day) * days)
    r = solve(rows, per_day, days)
    assert (-r['total_value'], r['total_hours'], len(r['chosen_indices']), tuple(r['chosen_indices'])) == key


def test_flags_not_claimed_and_no_mutation():
    rows = [('a', 1, 1)]
    snap = list(rows)
    r = solve(rows, 1, 1)
    assert rows == snap and r['sprint_outcome_validated'] is False and r['not_claimed'] is NOT_CLAIMED
    assert 'user testing results' in NOT_CLAIMED and 'feasibility' in NOT_CLAIMED
    assert r == solve(tuple(rows), 1, 1)


def test_cap_boundaries_accepted():
    twelve = [('f%d' % k, 1, 1) for k in range(12)]
    assert solve(twelve, 12, 1)['chosen'] == ['f%d' % k for k in range(12)]       # 4096 subsets
    assert solve([('a', 2**32 - 1, 2**32 - 1)], 2**32 - 1, 1)['total_value'] == 2**32 - 1
    assert solve([('a', F(1, 2**32 - 1), 0)], 1, 1)['total_value'] == F(1, 2**32 - 1)
    assert solve([('a', F(2**32 - 1, 7), 0)], 1, 1)['total_value'] == F(2**32 - 1, 7)
    assert solve([('a', F(2**20, 3), 0)], 1, 1)['total_value'] == F(2**20, 3)
    assert solve([('x' * 40, 1, 1)], 1, 5)['chosen'] == ['x' * 40]
    assert solve([('a', 1, 1)], F(1, 2**32 - 1), 5)['capacity_hours'] == F(5, 2**32 - 1)


OK = [('a', 1, 1)]


@pytest.mark.parametrize('args,error,message', [
    ((None, 1), TypeError, 'features must be a list or tuple'),
    (('ab', 1), TypeError, 'features must be a list or tuple'),
    (([], 1), ValueError, 'feature count must be between 1 and 12'),
    ((OK * 13, 1), ValueError, 'feature count must be between 1 and 12'),
    ((OK, 1, True), TypeError, 'days must be nonbool int'),
    ((OK, 1, 1.0), TypeError, 'days must be nonbool int'),
    ((OK, 1, 0), ValueError, 'days must be between 1 and 5'),
    ((OK, 1, 6), ValueError, 'days must be between 1 and 5'),
    ((OK, True), TypeError, 'values must be nonbool int or Fraction'),
    ((OK, 1.5), TypeError, 'values must be nonbool int or Fraction'),
    ((OK, float('nan')), TypeError, 'values must be nonbool int or Fraction'),
    ((OK, 0), ValueError, 'hours per day must be positive'),
    ((OK, -1), ValueError, 'hours per day must be positive'),
    (([5], 1), ValueError, 'each feature must be (id, value, hours)'),
    (([('a', 1)], 1), ValueError, 'each feature must be (id, value, hours)'),
    (([(5, 1, 1)], 1), TypeError, 'feature ids must be str'),
    (([('', 1, 1)], 1), ValueError, 'feature ids must be 1 to 40 characters'),
    (([('x' * 41, 1, 1)], 1), ValueError, 'feature ids must be 1 to 40 characters'),
    (([('a', 1, 1), ('a', 2, 2)], 1), ValueError, 'feature ids must be unique'),
    (([('a', True, 1)], 1), TypeError, 'values must be nonbool int or Fraction'),
    (([('a', 1, 1.5)], 1), TypeError, 'values must be nonbool int or Fraction'),
    (([('a', -1, 1)], 1), ValueError, 'values and hours must be nonnegative'),
    (([('a', 1, -1)], 1), ValueError, 'values and hours must be nonnegative'),
    (([('a', 2**32, 1)], 1), ValueError, 'values must fit 32 bits'),
    (([('a', 1, F(2**32, 3))], 1), ValueError, 'values must fit 32 bits'),
    (([('a', 1, F(1, 2**32))], 1), ValueError, 'values must fit 32 bits'),
])
def test_errors(args, error, message):
    with pytest.raises(error) as exc:
        solve(*args)
    assert type(exc.value) is error and str(exc.value) == message
