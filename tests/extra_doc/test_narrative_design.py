from fractions import Fraction as F
from itertools import product
import pytest
from sugarcode.extra_doc.narrative_design import align_story_gameplay as solve, NOT_CLAIMED


def oracle(beats, budget):
    """Independent: enumerate per-beat (mismatch, minutes) pairs, then pick lexicographic min."""
    per = [[(abs(F(i) - F(t)), F(m)) for i, m in opts] for t, opts in beats]
    best = None
    for k, combo in enumerate(product(*[list(enumerate(p)) for p in per])):
        mism = sum(c[1][0] for c in combo)
        mins = sum(c[1][1] for c in combo)
        if mins > budget:
            continue
        key = (mism, mins)
        if best is None or key < best[0]:
            best = (key, [c[0] for c in combo])
    return best


def test_hand_derived_literals():
    # beat targets 3 and 8. options beat0: (2,10) or (3,25); beat1: (8,30) or (6,5). budget 40
    # combos: (2,8):mm 1+0=1 min 40 ok ; (2,6): 1+2=3 min 15 ; (3,8): 0+0=0 min 55 over ; (3,6): 0+2=2 min 30
    r = solve([(3, [(2, 10), (3, 25)]), (8, [(8, 30), (6, 5)])], 40)
    assert r['option_indices'] == [0, 0] and r['total_mismatch'] == 1 and r['total_minutes'] == 40
    assert r['beat_mismatches'] == [1, 0] and r['feasible_count'] == 3 and r['aligned'] is False
    r = solve([(3, [(2, 10), (3, 25)]), (8, [(8, 30), (6, 5)])], 55)
    assert r['option_indices'] == [1, 0] and r['total_mismatch'] == 0 and r['aligned'] is True and r['feasible_count'] == 4
    assert type(r['total_mismatch']) is F


def test_ties_prefer_fewer_minutes_then_first():
    r = solve([(5, [(4, 20), (6, 10)])], 100)          # both mismatch 1 -> fewer minutes
    assert r['option_indices'] == [1] and r['total_minutes'] == 10
    r = solve([(5, [(4, 10), (6, 10)])], 100)          # fully tied -> first
    assert r['option_indices'] == [0]


def test_budget_is_inclusive_and_infeasible_raises():
    assert solve([(1, [(1, 7)])], 7)['option_indices'] == [0]
    with pytest.raises(ValueError, match='^no encounter selection fits the minutes budget$'):
        solve([(1, [(1, 7)])], 6)
    assert solve([(0, [(0, 0)])], 0)['total_minutes'] == 0


@pytest.mark.parametrize('beats,budget', [
    ([(3, [(1, 4), (5, 2), (3, 9)]), (F(7, 2), [(4, 1), (F(1, 2), 3)]), (0, [(2, 2), (0, 8)])], 12),
    ([(10, [(9, 5), (11, 5), (10, 30)]), (2, [(0, 1), (4, 1)])], 40),
    ([(F(1, 3), [(0, 1), (F(2, 3), 1), (F(1, 3), 5)])], 5),
    ([(4, [(1, 1)]), (4, [(7, 1)]), (4, [(4, 3), (5, 0)])], 3),
])
def test_matches_independent_oracle(beats, budget):
    (mm, mins), idx = oracle(beats, F(budget))
    r = solve(beats, budget)
    assert r['option_indices'] == idx and r['total_mismatch'] == mm and r['total_minutes'] == mins


def test_flags_and_not_claimed_and_no_mutation():
    b = [(2, [(1, 1), (2, 2)])]
    snap = [(2, [(1, 1), (2, 2)])]
    r = solve(b, 5)
    assert b == snap and r['story_quality_validated'] is False and r['not_claimed'] is NOT_CLAIMED
    assert 'story quality' in NOT_CLAIMED and 'player engagement or enjoyment' in NOT_CLAIMED
    assert r == solve(tuple((t, tuple(o)) for t, o in b), 5)


def test_cap_boundaries_accepted():
    beats = [(2, [(0, 1), (1, 1), (2, 1), (3, 1)])] * 6
    r = solve(beats, 6)
    assert r['feasible_count'] == 4096 and r['total_mismatch'] == 0
    assert solve([(2**32 - 1, [(2**32 - 1, 0)])], 2**32 - 1)['aligned'] is True
    assert solve([(F(1, 2**32 - 1), [(0, 0)])], 0)['total_mismatch'] == F(1, 2**32 - 1)
    assert solve([(F(2**32 - 1, 7), [(0, 0)])], 0)['total_mismatch'] == F(2**32 - 1, 7)
    assert solve([(F(2**20, 3), [(0, 0)])], 0)['total_mismatch'] == F(2**20, 3)


@pytest.mark.parametrize('args,error,message', [
    ((None, 1), TypeError, 'beats must be a list or tuple'),
    (('ab', 1), TypeError, 'beats must be a list or tuple'),
    (([], 1), ValueError, 'beat count must be between 1 and 6'),
    (([(1, [(1, 1)])] * 7, 1), ValueError, 'beat count must be between 1 and 6'),
    (([5], 1), ValueError, 'each beat must be (target_intensity, options)'),
    (([(1, [(1, 1)], 9)], 1), ValueError, 'each beat must be (target_intensity, options)'),
    (([(1, [])], 1), ValueError, 'each beat must have between 1 and 4 encounter options'),
    (([(1, [(1, 1)] * 5)], 1), ValueError, 'each beat must have between 1 and 4 encounter options'),
    (([(1, 'ab')], 1), ValueError, 'each beat must have between 1 and 4 encounter options'),
    (([(1, [(1,)])], 1), ValueError, 'options must contain intensity and minutes'),
    (([(1, [5])], 1), ValueError, 'options must contain intensity and minutes'),
    (([(True, [(1, 1)])], 1), TypeError, 'values must be nonbool int or Fraction'),
    (([(1, [(1.5, 1)])], 1), TypeError, 'values must be nonbool int or Fraction'),
    (([(1, [(1, float('nan'))])], 1), TypeError, 'values must be nonbool int or Fraction'),
    (([(1, [(1, 1)])], True), TypeError, 'values must be nonbool int or Fraction'),
    (([(1, [(1, 1)])], None), TypeError, 'values must be nonbool int or Fraction'),
    (([(1, [(1, 1)])], -1), ValueError, 'minutes budget must be nonnegative'),
    (([(-1, [(1, 1)])], 1), ValueError, 'intensities and minutes must be nonnegative'),
    (([(1, [(-1, 1)])], 1), ValueError, 'intensities and minutes must be nonnegative'),
    (([(1, [(1, -1)])], 1), ValueError, 'intensities and minutes must be nonnegative'),
    (([(2**32, [(1, 1)])], 1), ValueError, 'values must fit 32 bits'),
    (([(1, [(1, 1)])], F(2**32, 3)), ValueError, 'values must fit 32 bits'),
    (([(1, [(1, 1)])], F(1, 2**32)), ValueError, 'values must fit 32 bits'),
])
def test_errors(args, error, message):
    with pytest.raises(error) as exc:
        solve(*args)
    assert type(exc.value) is error and str(exc.value) == message
