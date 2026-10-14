from fractions import Fraction as F
from itertools import product
import pytest
from sugarcode.extra_doc.economy_design import balance_economy as solve, NOT_CLAIMED, _count


def oracle(faucets, sinks, target):
    """Independent brute force over rationals using Fraction sums of signed rates."""
    signed = [[F(v) for v in o] for o in faucets] + [[-F(v) for v in o] for o in sinks]
    best = None
    for combo in product(*[list(enumerate(g)) for g in signed]):
        net = sum(v for _, v in combo)
        fs = sum(v for (_, v), grp in zip(combo, range(len(signed))) if grp < len(faucets))
        key = (abs(net - F(target)), fs)
        if best is None or key < best[0]:
            best = (key, [i for i, _ in combo], net)
    return best


def test_hand_derived_literals():
    # options: faucet 10 or 20 ; sink 5 or 15. nets: 5, -5, 15, 5. target 0 -> gap 5 first at (0,0) (tie with (0,1))
    r = solve([[10, 20]], [[5, 15]], 100, 7)
    assert r['faucet_indices'] == [0] and r['sink_indices'] == [0]
    assert (r['faucet_total'], r['sink_total'], r['net_per_player_day'], r['imbalance']) == (10, 5, 5, 5)
    assert r['balanced'] is False and r['projected_supply_change'] == 5 * 100 * 7 == 3500
    assert r['candidate_count'] == 4
    # exact balance, rational rates: faucet 1/3 or 1/2, sink 1/6 or 1/3 -> (1/3,1/3) gives 0
    r = solve([[F(1, 3), F(1, 2)]], [[F(1, 6), F(1, 3)]], 3, 2)
    assert r['faucet_indices'] == [0] and r['sink_indices'] == [1]
    assert r['net_per_player_day'] == 0 and r['balanced'] is True and r['projected_supply_change'] == 0
    assert type(r['net_per_player_day']) is F


def test_target_negative_and_no_faucets_or_no_sinks():
    r = solve([], [[4, 7, 1]], 10, 1, -3)
    assert r['faucet_indices'] == [] and r['sink_indices'] == [0] and r['net_per_player_day'] == -4 and r['imbalance'] == 1
    assert r['projected_supply_change'] == -40   # nets -4,-7,-1 vs target -3: gaps 1,4,2
    r = solve([[2, 9]], [], 5, 2, 8)
    assert r['faucet_indices'] == [1] and r['sink_indices'] == [] and r['imbalance'] == 1


def test_tie_goes_to_smaller_faucet_total_then_first_candidate():
    # net 0 either way; (3 - 3) vs (5 - 5): smaller faucet total wins even though it is second
    r = solve([[5, 3]], [[5, 3]], 1, 1)
    assert r['faucet_indices'] == [1] and r['sink_indices'] == [1] and r['faucet_total'] == 3
    # identical totals: first candidate in option order
    r = solve([[3, 3]], [[3, 3]], 1, 1)
    assert r['faucet_indices'] == [0] and r['sink_indices'] == [0]


@pytest.mark.parametrize('faucets,sinks,target', [
    ([[1, 4], [2, 3]], [[3, 6], [0, 1]], 0),
    ([[F(1, 2), 2], [1]], [[F(3, 2), 1, 5]], F(-1, 4)),
    ([[7, 1, 4], [3, 3]], [[2], [6, 5], [1, 9]], 2),
    ([], [[1, 2, 3], [4, 5]], -5),
])
def test_matches_independent_bruteforce(faucets, sinks, target):
    (gap, fs), idx, net = oracle(faucets, sinks, target)
    r = solve(faucets, sinks, 7, 3, target)
    assert r['faucet_indices'] + r['sink_indices'] == idx
    assert r['imbalance'] == gap and r['faucet_total'] == fs and r['net_per_player_day'] == net
    assert r['projected_supply_change'] == net * 21


def test_flags_and_not_claimed():
    r = solve([[1]], [[1]], 1, 1)
    assert r['economy_health_validated'] is False and r['not_claimed'] is NOT_CLAIMED
    assert 'healthy or fair economy' in NOT_CLAIMED and 'monetization' in NOT_CLAIMED
    assert list(NOT_CLAIMED) == list(r['not_claimed'])


def test_cap_boundaries_accepted():
    big = [[0, 1, 2, 3]] * 6
    r = solve(big[:3], big[3:], 1000000, 3650)
    assert r['candidate_count'] == 4096
    assert solve([[2**32 - 1]], [[0]], 1, 1)['faucet_total'] == 2**32 - 1
    assert solve([[F(1, 2**32 - 1)]], [[0]], 1, 1)['faucet_total'] == F(1, 2**32 - 1)
    assert solve([[0]], [[0]], 1, 1, -(2**32 - 1))['imbalance'] == 2**32 - 1
    assert solve([[0]], [[0]], 1, 1)['projected_supply_change'] == 0


@pytest.mark.parametrize('args,error,message', [
    ((None, [[1]], 1, 1), TypeError, 'faucets must be a list or tuple'),
    (([[1]], 'ab', 1, 1), TypeError, 'sinks must be a list or tuple'),
    (([], [], 1, 1), ValueError, 'faucet and sink count together must be between 1 and 6'),
    (([[1]] * 4, [[1]] * 3, 1, 1), ValueError, 'faucet and sink count together must be between 1 and 6'),
    (([[]], [], 1, 1), ValueError, 'each faucet and sink must have between 1 and 4 rate options'),
    (([[1] * 5], [], 1, 1), ValueError, 'each faucet and sink must have between 1 and 4 rate options'),
    (([5], [], 1, 1), ValueError, 'each faucet and sink must have between 1 and 4 rate options'),
    (([[1]], [], True, 1), TypeError, 'players and days must be nonbool int'),
    (([[1]], [], 1, True), TypeError, 'players and days must be nonbool int'),
    (([[1]], [], 1.0, 1), TypeError, 'players and days must be nonbool int'),
    (([[1]], [], 0, 1), ValueError, 'players must be between 1 and 1000000'),
    (([[1]], [], 1000001, 1), ValueError, 'players must be between 1 and 1000000'),
    (([[1]], [], 1, 0), ValueError, 'days must be between 1 and 3650'),
    (([[1]], [], 1, 3651), ValueError, 'days must be between 1 and 3650'),
    (([[True]], [], 1, 1), TypeError, 'values must be nonbool int or Fraction'),
    (([[1.5]], [], 1, 1), TypeError, 'values must be nonbool int or Fraction'),
    (([[float('nan')]], [], 1, 1), TypeError, 'values must be nonbool int or Fraction'),
    (([[1]], [[None]], 1, 1), TypeError, 'values must be nonbool int or Fraction'),
    (([[-1]], [], 1, 1), ValueError, 'rates must be nonnegative'),
    (([[1]], [[F(-1, 2)]], 1, 1), ValueError, 'rates must be nonnegative'),
    (([[2**32]], [], 1, 1), ValueError, 'values must fit 32 bits'),
    (([[F(2**32, 3)]], [], 1, 1), ValueError, 'values must fit 32 bits'),
    (([[F(1, 2**32)]], [], 1, 1), ValueError, 'values must fit 32 bits'),
])
def test_errors(args, error, message):
    with pytest.raises(error) as exc:
        solve(*args)
    assert type(exc.value) is error and str(exc.value) == message


def test_target_bool_float_and_bits_refused():
    for bad, error in ((True, TypeError), (0.5, TypeError), (2**32, ValueError), (F(1, 2**32), ValueError)):
        with pytest.raises(error):
            solve([[1]], [[1]], 1, 1, bad)


def test_inputs_not_mutated_and_tuples_accepted():
    f, s = [[3, 1]], [[2, 5]]
    snap = ([list(x) for x in f], [list(x) for x in s])
    a = solve(f, s, 2, 2)
    assert (f, s) == snap
    assert a == solve(((3, 1),), ((2, 5),), 2, 2)


def test_count_helper():
    assert _count([[1, 2], [1, 2, 3]]) == 6 and _count([]) == 1


def test_equal_gap_and_faucet_total_keeps_first_candidate():
    # sinks 5 or 1 with faucet 3: nets -2 and +2, both gap 2 and fsum 3 -> first candidate (sink index 0)
    r = solve([[3]], [[5, 1]], 1, 1)
    assert r['sink_indices'] == [0] and r['net_per_player_day'] == -2 and r['imbalance'] == 2
    r = solve([[3]], [[1, 5]], 1, 1)
    assert r['sink_indices'] == [0] and r['net_per_player_day'] == 2


def test_numerator_bit_boundary_exact():
    assert solve([[F(2**32 - 1, 7)]], [[0]], 1, 1)['faucet_total'] == F(2**32 - 1, 7)   # 32-bit numerator accepted
    assert solve([[F(2**20, 3)]], [[0]], 1, 1)['faucet_total'] == F(2**20, 3)
    with pytest.raises(ValueError, match='^values must fit 32 bits$'):
        solve([[F(2**32, 3)]], [[0]], 1, 1)
    with pytest.raises(ValueError, match='^values must fit 32 bits$'):
        solve([[F(1, 2**32)]], [[0]], 1, 1)
    assert solve([[F(1, 2**32 - 1)]], [[0]], 1, 1)['faucet_total'] == F(1, 2**32 - 1)
