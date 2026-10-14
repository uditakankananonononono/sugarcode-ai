import random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.expert_advice import aggregate_experts as agg


def test_hand_case():
    r = agg([[1, 0], [1, 0]], F(1, 2))
    assert r['mixtures'] == [[F(1, 2), F(1, 2)], [F(1, 3), F(2, 3)]]
    assert r['learner_loss'] == F(5, 6) and r['expert_losses'] == [2, 0]
    assert r['regret_vs_expert'] == [F(-7, 6), F(5, 6)] and r['best_expert'] == 1
    assert r['final_weights'] == [F(1, 4), 1]
    # one expert: the mixture is always that expert, regret is 0
    r = agg([[F(1, 3)], [1], [0]], F(1, 2))
    assert r['mixtures'] == [[1]] * 3 and r['regret_vs_expert'] == [0]
    # ties go to the lowest index
    assert agg([[F(1, 2), F(1, 2), 1]], F(1, 2))['best_expert'] == 0
    # prior-round weights: round 1 is always uniform whatever the losses are
    assert agg([[1, 0, 0]], F(1, 2))['mixtures'][0] == [F(1, 3)] * 3


def test_independent_oracle_closed_form_weights():
    rnd = random.Random(21)
    for _ in range(300):
        n, T = rnd.randint(1, 5), rnd.randint(1, 8)
        L = [[F(rnd.randint(0, 6), 6) for _ in range(n)] for _ in range(T)]
        eta = F(rnd.randint(1, 5), 10)
        r = agg(L, eta)
        total = F(0)
        for t in range(T):
            w = []
            for i in range(n):
                prod = F(1)
                for s in range(t):
                    prod *= 1 - eta * L[s][i]      # weight from scratch: product over earlier rounds only
                w.append(prod)
            p = [v / sum(w) for v in w]
            assert r['mixtures'][t] == p and sum(p) == 1
            total += sum(p[i] * L[t][i] for i in range(n))
        assert r['learner_loss'] == total
        cum = [sum(L[t][i] for t in range(T)) for i in range(n)]
        assert r['expert_losses'] == cum and r['regret_vs_expert'] == [total - c for c in cum]
        assert cum[r['best_expert']] == min(cum) and all(cum[j] > min(cum) for j in range(r['best_expert']))


def test_boundaries_and_caps():
    big = 2 ** 32 - 1
    assert agg([[F(1, big)]], F(1, big))
    assert agg([[0, 1]] * 16, F(1, 2)) and agg([[0] * 5], F(1, 2)) and agg([[1], [0]], F(1, 2))
    for bad in (2 ** 32, F(1, 2 ** 32), F(2 ** 32, 3)):
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            agg([[bad]], F(1, 2))
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            agg([[0]], bad)
    assert agg([[1]], F(1, 2)) and agg([[0]], F(1, 1000))


@pytest.mark.parametrize('args,err,msg', [
    (('x', F(1, 2)), TypeError, 'losses must be a list or tuple of rounds'),
    (([], F(1, 2)), ValueError, 'rounds must be between 1 and 16'),
    (([[0]] * 17, F(1, 2)), ValueError, 'rounds must be between 1 and 16'),
    (([0], F(1, 2)), TypeError, 'losses must be a list or tuple of rounds'),
    (([[]], F(1, 2)), ValueError, 'experts must be between 1 and 5'),
    (([[0] * 6], F(1, 2)), ValueError, 'experts must be between 1 and 5'),
    (([[0] * 6, [0]], F(1, 2)), ValueError, 'experts must be between 1 and 5'),
    (([[0, 0], [0]], F(1, 2)), ValueError, 'every round must have the same number of experts'),
    (([[True]], F(1, 2)), TypeError, 'values must be nonbool int or Fraction'),
    (([[0.5]], F(1, 2)), TypeError, 'values must be nonbool int or Fraction'),
    (([[0]], True), TypeError, 'values must be nonbool int or Fraction'),
    (([[-1]], F(1, 2)), ValueError, r'losses must be in \[0, 1\]'),
    (([[2]], F(1, 2)), ValueError, r'losses must be in \[0, 1\]'),
    (([[0], [F(3, 2)]], F(1, 2)), ValueError, r'losses must be in \[0, 1\]'),
    (([[0]], 0), ValueError, r'eta must be in \(0, 1/2\]'),
    (([[0]], F(3, 5)), ValueError, r'eta must be in \(0, 1/2\]'),
    (([[0]], -1), ValueError, r'eta must be in \(0, 1/2\]'),
])
def test_exact_errors(args, err, msg):
    with pytest.raises(err, match='^' + msg + '$'):
        agg(*args)


def test_mixed_valid_and_invalid_losses_every_position():
    for pos in range(4):
        flat = [F(1, 2)] * 4
        flat[pos] = F(-1, 2) if pos % 2 else F(3, 2)
        with pytest.raises(ValueError, match=r'^losses must be in \[0, 1\]$'):
            agg([flat[:2], flat[2:]], F(1, 2))


def test_numerator_32_bit_boundary_and_non_sequence_input():
    big = 2 ** 32 - 1
    assert agg([[F(big - 1, big)]], F(1, 2))          # numerator has exactly 32 bits
    with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
        agg([[F(2 ** 32, 2 ** 32 + 1)]], F(1, 2))      # numerator 33 bits only
    for bad in (5, None, {0: [0]}):
        with pytest.raises(TypeError, match='^losses must be a list or tuple of rounds$'):
            agg(bad, F(1, 2))
