import random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.regret_matching import regret_matching as rm


def test_hand_case():
    r = rm([[1, 0], [1, 0]])
    assert r['policies'] == [[F(1, 2), F(1, 2)], [1, 0]]
    assert r['round_payoffs'] == [F(1, 2), 1] and r['total_payoff'] == F(3, 2)
    assert r['cumulative_regret'] == [F(1, 2), F(-3, 2)]
    assert r['average_policy'] == [F(3, 4), F(1, 4)] and r['external_regret'] == F(1, 2)
    # no positive regret ever: stays uniform (identical payoffs)
    r = rm([[F(1, 2)] * 3] * 4)
    assert r['policies'] == [[F(1, 3)] * 3] * 4 and r['cumulative_regret'] == [0, 0, 0]
    # one action
    assert rm([[1], [0]])['external_regret'] == 0


def test_independent_oracle_and_identity():
    rnd = random.Random(8)
    for _ in range(300):
        n, T = rnd.randint(1, 5), rnd.randint(1, 8)
        U = [[F(rnd.randint(0, 8), 8) for _ in range(n)] for _ in range(T)]
        r = rm(U)
        # independent bookkeeping: regret of action i = (sum of its payoffs) - (total earned), recomputed from policies
        tot = sum(sum(r['policies'][t][i] * U[t][i] for i in range(n)) for t in range(T))
        assert r['total_payoff'] == tot
        for i in range(n):
            assert r['cumulative_regret'][i] == sum(U[t][i] for t in range(T)) - tot
        # policies from the definition: proportional to positive part of regret up to the previous round
        for t in range(T):
            reg = [sum(U[s][i] - sum(r['policies'][s][k] * U[s][k] for k in range(n)) for s in range(t)) for i in range(n)]
            pos = [x if x > 0 else 0 for x in reg]
            exp = [F(1, n)] * n if sum(pos) == 0 else [x / sum(pos) for x in pos]
            assert r['policies'][t] == exp and sum(exp) == 1
        assert r['average_policy'] == [sum(p[i] for p in r['policies']) / T for i in range(n)]
        assert r['external_regret'] == max(r['cumulative_regret'])


def test_boundaries_and_caps():
    big = 2 ** 32 - 1
    assert rm([[F(1, big)]])
    assert rm([[0, 1]] * 10) and rm([[0] * 5]) and rm([[1]])
    for bad in (2 ** 32, F(1, 2 ** 32), F(2 ** 32, 3)):
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            rm([[bad]])


@pytest.mark.parametrize('payoffs,err,msg', [
    ('x', TypeError, 'payoffs must be a list or tuple of rounds'),
    ([], ValueError, 'rounds must be between 1 and 10'),
    ([[0]] * 11, ValueError, 'rounds must be between 1 and 10'),
    ([0], TypeError, 'payoffs must be a list or tuple of rounds'),
    ([[]], ValueError, 'actions must be between 1 and 5'),
    ([[0] * 6], ValueError, 'actions must be between 1 and 5'),
    ([[0] * 6, [0]], ValueError, 'actions must be between 1 and 5'),
    ([[0, 0], [0]], ValueError, 'every round must have the same number of actions'),
    ([[True]], TypeError, 'values must be nonbool int or Fraction'),
    ([[1.0]], TypeError, 'values must be nonbool int or Fraction'),
    ([[-1]], ValueError, r'payoffs must be in \[0, 1\]'),
    ([[2]], ValueError, r'payoffs must be in \[0, 1\]'),
])
def test_exact_errors(payoffs, err, msg):
    with pytest.raises(err, match='^' + msg + '$'):
        rm(payoffs)


def test_mixed_valid_and_invalid_payoffs_every_position():
    for pos in range(4):
        flat = [F(1, 2)] * 4
        flat[pos] = F(-1, 2) if pos % 2 else F(3, 2)
        with pytest.raises(ValueError, match=r'^payoffs must be in \[0, 1\]$'):
            rm([flat[:2], flat[2:]])


def test_numerator_32_bit_boundary_and_non_sequence_input():
    big = 2 ** 32 - 1
    assert rm([[F(big - 1, big)]])
    with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
        rm([[F(2 ** 32, 2 ** 32 + 1)]])
    for bad in (5, None, {0: [0]}):
        with pytest.raises(TypeError, match='^payoffs must be a list or tuple of rounds$'):
            rm(bad)
