import itertools
import random
from fractions import Fraction as F
from math import gcd

import pytest

import sugarcode.extra_doc.finite_markov_exact as m
from sugarcode.extra_doc.finite_markov_exact import (
    absorption_probabilities, class_periods, communicating_classes, expected_steps_to_absorption,
    fundamental_matrix, hitting_probabilities, is_strongly_lumpable, mean_first_passage_times,
    stationary_distributions, total_variation_to_stationary)

CLAIMS_OFF = {'forecast': False, 'estimation_from_data': False, 'model_adequacy': False,
              'mixing_time_bound': False}
E_WTYPE = 'W must be a list or tuple'
E_WN = 'W row count must be between 1 and 7'
E_ROWT = 'W rows must be lists or tuples'
E_ROWL = 'W row length must equal the row count'
E_ENT = 'W entries must be nonbool int'
E_RNG = 'W entries must be between 0 and 1000'
E_SUM = 'W row sums must be positive'


# ---------------- independent oracles ----------------
def o_P(W):
    return [[F(v, sum(r)) for v in r] for r in W]


def o_det(M):
    """Laplace expansion (cofactors), unrelated to the module's Gauss-Jordan."""
    n = len(M)
    if n == 0:
        return F(1)
    if n == 1:
        return M[0][0]
    return sum((-1) ** j * M[0][j] * o_det([r[:j] + r[j + 1:] for r in M[1:]]) for j in range(n) if M[0][j] != 0)


def o_cramer(A, b):
    d = o_det(A)
    assert d != 0
    out = []
    for c in range(len(A)):
        Ac = [r[:c] + [b[i]] + r[c + 1:] for i, r in enumerate(A)]
        out.append(o_det(Ac) / d)
    return out


def o_matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]


def o_reach_by_powers(W):
    n = len(W)
    A = [[1 if (i == j or W[i][j] > 0) else 0 for j in range(n)] for i in range(n)]
    R = A
    for _ in range(n):
        R = [[1 if sum(R[i][k] * A[k][j] for k in range(n)) else 0 for j in range(n)] for i in range(n)]
    return R


def o_classes(W):
    n = len(W)
    R = o_reach_by_powers(W)
    cls = {}
    for i in range(n):
        key = tuple(j for j in range(n) if R[i][j] and R[j][i])
        cls[key] = True
    out = []
    for key in sorted(cls):
        closed = all(not (W[i][j] > 0) for i in key for j in range(n) if j not in key)
        out.append((list(key), closed))
    return sorted(out)


def o_period(W, cls):
    n = len(W)
    A = [[1 if W[i][j] > 0 else 0 for j in range(n)] for i in range(n)]
    g = 0
    Pw = A
    for t in range(1, 2 * n * n + 1):
        if Pw[cls[0]][cls[0]]:
            g = gcd(g, t)
        Pw = [[1 if sum(Pw[i][k] * A[k][j] for k in range(n)) else 0 for j in range(n)] for i in range(n)]
    return g


def o_tree_stationary(P, cls):
    """Markov chain tree theorem form: pi_j proportional to the principal minor of I-P at j."""
    k = len(cls)
    M = [[(1 if a == b else 0) - P[cls[a]][cls[b]] for b in range(k)] for a in range(k)]
    D = []
    for j in range(k):
        sub = [[M[a][b] for b in range(k) if b != j] for a in range(k) if a != j]
        D.append(o_det(sub))
    s = sum(D)
    return [d / s for d in D]


def o_random_W(rnd, n, hi=3, zero_p=0.4):
    while True:
        W = [[0 if rnd.random() < zero_p else rnd.randint(1, hi) for _ in range(n)] for _ in range(n)]
        if all(sum(r) > 0 for r in W):
            return W


def o_dist_steps(P, start, k):
    n = len(P)
    mu = [F(int(i == start)) for i in range(n)]
    out = [mu]
    for _ in range(k):
        mu = [sum(mu[i] * P[i][j] for i in range(n)) for j in range(n)]
        out.append(mu)
    return out


def o_hit_series(P, targets, steps):
    """P(hit within `steps`) by exact propagation with the targets made absorbing."""
    n = len(P)
    Q = [[F(int(i == j)) if i in targets else P[i][j] for j in range(n)] for i in range(n)]
    h = []
    for s in range(n):
        mu = [F(int(i == s)) for i in range(n)]
        for _ in range(steps):
            mu = [sum(mu[i] * Q[i][j] for i in range(n)) for j in range(n)]
        h.append(sum(mu[t] for t in targets))
    return h


def o_set_partitions(items):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for p in o_set_partitions(rest):
        for i in range(len(p)):
            yield p[:i] + [[first] + p[i]] + p[i + 1:]
        yield [[first]] + p


SMALL = [[[a, b], [c, d]] for a, b, c, d in itertools.product(range(3), repeat=4) if a + b and c + d]
ALL3 = [[list(W[0:3]), list(W[3:6]), list(W[6:9])] for W in itertools.product(range(3), repeat=9)
        if W[0] + W[1] + W[2] and W[3] + W[4] + W[5] and W[6] + W[7] + W[8]]
_rnd = random.Random(495)
RAND = [o_random_W(_rnd, n) for n in (3, 4, 5, 6, 7) for _ in range(12)] + \
       [o_random_W(_rnd, n, 2, 0.6) for n in (4, 5) for _ in range(30)]


# ---------------- agreement with oracles ----------------
def test_classes_match_reachability_by_powers_exhaustive_n3():
    for W in SMALL + ALL3 + RAND:
        got = [(c['states'], c['closed']) for c in communicating_classes(W)['classes']]
        assert got == o_classes(W), W
        assert sorted(s for c, _ in got for s in c) == list(range(len(W)))


def test_periods_match_return_time_gcd_exhaustive_n3():
    for W in SMALL + ALL3 + RAND:
        got = class_periods(W)['periods']
        want = [{'states': c, 'period': o_period(W, c)} for c, k in o_classes(W) if k]
        assert got == want, W


def test_fundamental_matrix_matches_cramer_inverse():
    for W in ALL3[::37] + RAND:
        P = o_P(W)
        r = fundamental_matrix(W)
        T = r['transient']
        assert T == sorted(s for c, k in o_classes(W) if not k for s in c)
        if not T:
            assert r['matrix'] == []
            continue
        IQ = [[(1 if a == b else 0) - P[i][j] for b, j in enumerate(T)] for a, i in enumerate(T)]
        N = r['matrix']
        cols = [o_cramer(IQ, [F(int(a == c)) for a in range(len(T))]) for c in range(len(T))]
        assert N == [[cols[c][a] for c in range(len(T))] for a in range(len(T))]
        assert o_matmul(IQ, N) == [[F(int(a == b)) for b in range(len(T))] for a in range(len(T))]
        assert all(x >= 0 for row in N for x in row)


def test_absorption_probabilities_and_times_satisfy_defining_equations():
    for W in ALL3[::23] + RAND:
        P = o_P(W)
        ab = absorption_probabilities(W)
        st = expected_steps_to_absorption(W)
        T, C = ab['transient'], ab['closed_classes']
        assert st['transient'] == T and C == [c for c, k in o_classes(W) if k]
        for a, i in enumerate(T):
            assert sum(ab['probabilities'][a]) == 1
            for ci, c in enumerate(C):
                rhs = sum(P[i][j] for j in c) + sum(P[i][t] * ab['probabilities'][b][ci] for b, t in enumerate(T))
                assert ab['probabilities'][a][ci] == rhs
            assert st['steps'][a] == 1 + sum(P[i][t] * st['steps'][b] for b, t in enumerate(T))
            assert st['steps'][a] >= 1
        # uniqueness: the system matrix is nonsingular
        if T:
            IQ = [[(1 if a == b else 0) - P[i][j] for b, j in enumerate(T)] for a, i in enumerate(T)]
            assert o_det(IQ) != 0


def test_hand_values_gamblers_ruin_and_known_chain():
    W = [[1, 0, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 0, 1]]
    ab = absorption_probabilities(W)
    assert ab['transient'] == [1, 2] and ab['closed_classes'] == [[0], [3]]
    assert ab['probabilities'] == [[F(2, 3), F(1, 3)], [F(1, 3), F(2, 3)]]
    assert expected_steps_to_absorption(W)['steps'] == [F(2), F(2)]
    assert fundamental_matrix(W)['matrix'] == [[F(4, 3), F(2, 3)], [F(2, 3), F(4, 3)]]
    assert hitting_probabilities(W, [3])['probabilities'] == [F(0), F(1, 3), F(2, 3), F(1)]
    assert mean_first_passage_times(W, [3])['times'] == [None, None, None, F(0)]
    assert mean_first_passage_times(W, [0, 3])['times'] == [F(0), F(2), F(2), F(0)]
    assert stationary_distributions(W)['unique'] is False
    assert stationary_distributions(W)['distributions'] == [
        {'states': [0], 'distribution': [F(1)]}, {'states': [3], 'distribution': [F(1)]}]
    # two-state chain with P = [[2/3, 1/3], [1/2, 1/2]]: pi = (3/5, 2/5), first passage 0 -> 1 is 3
    W2 = [[2, 1], [1, 1]]
    assert stationary_distributions(W2)['distributions'][0]['distribution'] == [F(3, 5), F(2, 5)]
    assert mean_first_passage_times(W2, [1])['times'] == [F(3), F(0)]
    assert mean_first_passage_times(W2, [0])['times'] == [F(0), F(2)]


def test_stationary_matches_tree_theorem_and_fixed_point():
    for W in ALL3[::19] + RAND:
        P = o_P(W)
        res = stationary_distributions(W)
        want_classes = [c for c, k in o_classes(W) if k]
        assert [d['states'] for d in res['distributions']] == want_classes
        assert res['unique'] == (len(want_classes) == 1)
        for d in res['distributions']:
            pi = d['distribution']
            c = d['states']
            assert pi == o_tree_stationary(P, c)
            assert sum(pi) == 1 and all(x > 0 for x in pi)
            for b, j in enumerate(c):
                assert sum(pi[a] * P[i][j] for a, i in enumerate(c)) == pi[b]


def test_periodic_chain_stationary_and_cesaro():
    W = [[0, 1, 0], [0, 0, 1], [2, 0, 0]]
    assert class_periods(W)['periods'][0]['period'] == 3
    pi = stationary_distributions(W)['distributions'][0]['distribution']
    assert pi == [F(1, 3)] * 3
    P = o_P(W)
    steps = o_dist_steps(P, 0, 30)
    avg = [sum(s[j] for s in steps[:30]) / 30 for j in range(3)]
    assert avg == pi
    with pytest.raises(ValueError) as e:
        total_variation_to_stationary(W, 0, 3)
    assert str(e.value) == 'chain must be irreducible and aperiodic'


def test_hitting_probabilities_equations_and_series():
    rnd = random.Random(8)
    for W in RAND[:40] + ALL3[::101]:
        n = len(W)
        P = o_P(W)
        for _ in range(3):
            tg = sorted(rnd.sample(range(n), rnd.randint(1, min(2, n))))
            h = hitting_probabilities(W, tg)['probabilities']
            for i in range(n):
                if i in tg:
                    assert h[i] == 1
                else:
                    assert h[i] == sum(P[i][j] * h[j] for j in range(n))
            lower = o_hit_series(P, tg, 25)
            assert all(lo <= x for lo, x in zip(lower, h))
            if len(W) <= 3:
                lower = o_hit_series(P, tg, 200)
                assert all(x - lo < F(1, 10 ** 3) for lo, x in zip(lower, h))
            # states that cannot reach the targets have exactly 0, others are positive
            R = o_reach_by_powers(W)
            for i in range(n):
                assert (h[i] > 0) == any(R[i][t] for t in tg)


def test_mean_first_passage_equations_and_series():
    rnd = random.Random(9)
    for W in RAND[:40] + ALL3[::101]:
        n = len(W)
        P = o_P(W)
        for _ in range(3):
            tg = sorted(rnd.sample(range(n), rnd.randint(1, min(2, n))))
            h = hitting_probabilities(W, tg)['probabilities']
            t = mean_first_passage_times(W, tg)['times']
            for i in range(n):
                if i in tg:
                    assert t[i] == 0
                elif h[i] == 1:
                    assert t[i] == 1 + sum(P[i][j] * t[j] for j in range(n) if j not in tg and P[i][j] > 0)
                    assert t[i] >= 1
                else:
                    assert t[i] is None
            if n <= 4:
                # E[T] = sum_k P(T > k): partial sums from below, tail small
                for i in range(n):
                    if t[i] is None:
                        continue
                    Q = [[F(int(a == b)) if a in tg else P[a][b] for b in range(n)] for a in range(n)]
                    mu = [F(int(a == i)) for a in range(n)]
                    tot = F(0)
                    for _ in range(250):
                        tot += 1 - sum(mu[x] for x in tg)
                        mu = [sum(mu[a] * Q[a][b] for a in range(n)) for b in range(n)]
                    assert tot <= t[i]
                    if t[i] <= 6:
                        assert t[i] - tot < F(1, 10 ** 2)


def test_lumpability_matches_dynkin_brute_force_and_dynamics():
    for W in SMALL + RAND[:25]:
        n = len(W)
        if n > 5:
            continue
        P = o_P(W)
        for part in o_set_partitions(list(range(n))):
            ok = True
            for A in part:
                for B in part:
                    if len({sum(P[i][j] for j in B) for i in A}) > 1:
                        ok = False
            r = is_strongly_lumpable(W, part)
            assert r['lumpable'] == ok, (W, part)
            if ok:
                L = r['lumped_matrix']
                assert all(sum(row) == 1 for row in L)
                for a, A in enumerate(part):
                    base = o_dist_steps(P, A[0], 3)[-1]
                    lumped_start = [F(int(b == a)) for b in range(len(part))]
                    for _ in range(3):
                        lumped_start = [sum(lumped_start[x] * L[x][y] for x in range(len(part)))
                                        for y in range(len(part))]
                    assert [sum(base[j] for j in B) for B in part] == lumped_start
            else:
                assert r['lumped_matrix'] is None
    assert is_strongly_lumpable([[1, 1, 0], [1, 1, 0], [0, 0, 1]], [[0, 1], [2]])['lumpable'] is True
    assert is_strongly_lumpable([[1, 2], [3, 1]], [[0], [1]])['lumped_matrix'] == [
        [F(1, 3), F(2, 3)], [F(3, 4), F(1, 4)]]
    # trivial partitions: one block always lumps; singletons always lump
    assert is_strongly_lumpable([[1, 2], [3, 1]], [[1, 0]])['lumped_matrix'] == [[F(1)]]


def test_total_variation_matches_direct_propagation():
    for W in SMALL + RAND:
        n = len(W)
        cl = o_classes(W)
        erg = len(cl) == 1 and cl[0][1] and o_period(W, cl[0][0]) == 1
        for start in range(n):
            if not erg:
                with pytest.raises(ValueError):
                    total_variation_to_stationary(W, start, 1)
                break
            P = o_P(W)
            pi = o_tree_stationary(P, list(range(n)))
            seq = o_dist_steps(P, start, 6)
            for k in (0, 1, 2, 5, 6):
                r = total_variation_to_stationary(W, start, k)
                assert r['distribution'] == seq[k] and r['stationary'] == pi
                assert r['tv'] == sum(abs(a - b) for a, b in zip(seq[k], pi)) / 2
                assert 0 <= r['tv'] <= 1
    r64 = total_variation_to_stationary([[1, 1], [1, 2]], 0, 64)
    assert 0 < r64['tv'] < F(1, 10 ** 10)
    assert total_variation_to_stationary([[5]], 0, 0)['tv'] == 0
    assert total_variation_to_stationary([[1, 1], [1, 1]], 0, 0)['tv'] == F(1, 2)
    assert total_variation_to_stationary([[1, 1], [1, 1]], 0, 1)['tv'] == 0


# ---------------- hardening ----------------
def _whole(W):
    try:
        return [list(range(len(W)))]
    except TypeError:
        return [[0]]


W_FUNCS = [communicating_classes, class_periods, fundamental_matrix, absorption_probabilities,
           expected_steps_to_absorption, stationary_distributions,
           lambda W: hitting_probabilities(W, [0]), lambda W: mean_first_passage_times(W, [0]),
           lambda W: is_strongly_lumpable(W, _whole(W)),
           lambda W: total_variation_to_stationary(W, 0, 1)]
W_NAMES = ['communicating_classes', 'class_periods', 'fundamental_matrix', 'absorption_probabilities',
           'expected_steps_to_absorption', 'stationary_distributions', 'hitting_probabilities',
           'mean_first_passage_times', 'is_strongly_lumpable', 'total_variation_to_stationary']


class Boom:
    __hash__ = None

    def __eq__(self, other):
        raise AssertionError('touched')

    def __index__(self):
        raise AssertionError('touched')


@pytest.mark.parametrize('f', W_FUNCS)
def test_W_refusals_pinned(f):
    ok7 = [[1] * 7 for _ in range(7)]
    f(ok7)
    f([[1]])
    f(tuple(tuple(r) for r in ok7))
    for bad in (None, 5, 'ab', b'ab', {0: [1]}, {1}, iter([[1]]), 1.5, range(2)):
        with pytest.raises(TypeError) as e:
            f(bad)
        assert str(e.value) == E_WTYPE

    class L(list):
        pass
    with pytest.raises(TypeError) as e:
        f(L([[1]]))
    assert str(e.value) == E_WTYPE
    for n in (0, 8, 9, 100):                     # count refused before any row is read
        with pytest.raises(ValueError) as e:
            f([Boom()] * n)
        assert str(e.value) == E_WN
    for bad in (None, 3, 'a', {0: 1}, {1, 2}, iter([1])):
        with pytest.raises(TypeError) as e:
            f([bad])
        assert str(e.value) == E_ROWT
    for bad in ([1, 1], [], [1, 1, 1]):
        with pytest.raises(ValueError) as e:
            f([bad, [1, 1]][:2] if len(bad) != 2 else [[1], [1]])
        assert str(e.value) == E_ROWL
    with pytest.raises(ValueError) as e:
        f([[1, 1, 1], [1, 1, 1]])
    assert str(e.value) == E_ROWL
    for bad in (True, False, 1.0, '1', None, [1], (1,), {}, set(), Boom(), 1j):
        with pytest.raises(TypeError) as e:       # unhashable and weird entries: type first
            f([[bad]])
        assert str(e.value) == E_ENT
    for bad in (-1, 1001, 10 ** 30, -10 ** 30):
        with pytest.raises(ValueError) as e:
            f([[bad]])
        assert str(e.value) == E_RNG
    f([[1000]])
    f([[1, 1000], [1000, 0]])
    with pytest.raises(ValueError) as e:
        f([[0]])
    assert str(e.value) == E_SUM
    with pytest.raises(ValueError) as e:
        f([[0, 0], [1, 1]])
    assert str(e.value) == E_SUM


@pytest.mark.parametrize('f', W_FUNCS)
def test_W_first_bad_order(f):
    # row 0 sum bad, row 1 has a bad entry type: sum of row 0 is checked when row 0 ends
    with pytest.raises(ValueError) as e:
        f([[0, 0], [True, 1]])
    assert str(e.value) == E_SUM
    # within a row, an out-of-range int before a bad type: first entry wins
    with pytest.raises(ValueError) as e:
        f([[1001, True], [1, 1]])
    assert str(e.value) == E_RNG
    with pytest.raises(TypeError) as e:
        f([[True, 1001], [1, 1]])
    assert str(e.value) == E_ENT
    # row length before entries
    with pytest.raises(ValueError) as e:
        f([[True], [1, 1]])
    assert str(e.value) == E_ROWL
    # row type before the next row's length
    with pytest.raises(TypeError) as e:
        f([[1, 1], 'ab'])
    assert str(e.value) == E_ROWT
    # count before row types
    with pytest.raises(ValueError) as e:
        f([None] * 8)
    assert str(e.value) == E_WN


@pytest.mark.parametrize('f', W_FUNCS[:6])
def test_unary_functions_results_untouched_inputs_claims(f):
    W = [[1, 2, 0], [0, 1, 1], [1, 0, 1]]
    c = [list(r) for r in W]
    r = f(W)
    assert W == c and r['n'] == 3
    assert r['claims'] == CLAIMS_OFF and all(v is False for v in r['claims'].values())
    r['claims']['forecast'] = True
    assert m.CLAIMS['forecast'] is False
    assert f(tuple(tuple(x) for x in W)) == f(W)


def test_targets_refusals():
    W = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    for f in (hitting_probabilities, mean_first_passage_times):
        f(W, [0, 1, 2])
        f(W, (2,))
        for bad in (None, 5, '01', {0}, iter([0]), range(1)):
            with pytest.raises(TypeError) as e:
                f(W, bad)
            assert str(e.value) == 'targets must be a list or tuple'
        for n in (0, 4, 10):                       # length before entries
            with pytest.raises(ValueError) as e:
                f(W, [Boom()] * n)
            assert str(e.value) == 'targets length must be between 1 and 3'
        for bad in (True, 0.0, '0', None, [0], Boom()):
            with pytest.raises(TypeError) as e:
                f(W, [bad])
            assert str(e.value) == 'targets entries must be nonbool int'
        for bad in (3, -1, 10 ** 30):
            with pytest.raises(ValueError) as e:
                f(W, [bad])
            assert str(e.value) == 'targets entries must be between 0 and 2'
        with pytest.raises(ValueError) as e:
            f(W, [1, 1])
        assert str(e.value) == 'targets entries must be distinct'
        with pytest.raises(ValueError) as e:
            f(W, [3, True])
        assert str(e.value) == 'targets entries must be between 0 and 2'
        with pytest.raises(ValueError) as e:       # W first
            f([[0]], [5])
        assert str(e.value) == E_SUM
    r = hitting_probabilities(W, (2, 0))
    assert r['targets'] == [0, 2] and r['claims'] == CLAIMS_OFF
    assert mean_first_passage_times(W, [1])['times'] == [F(3), F(0), F(3)]


def test_partition_refusals():
    W = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    f = is_strongly_lumpable
    f(W, [[0], [1], [2]])
    f(W, ([2, 0], (1,)))
    for bad in (None, 5, '01', {0}, iter([[0]]), range(1)):
        with pytest.raises(TypeError) as e:
            f(W, bad)
        assert str(e.value) == 'partition must be a list or tuple'
    for blocks in ([], [[0]] * 4, [[0]] * 9):      # count before blocks are read
        with pytest.raises(ValueError) as e:
            f(W, blocks if blocks else [])
        assert str(e.value) == 'partition block count must be between 1 and 3'
    with pytest.raises(ValueError) as e:
        f(W, [Boom()] * 4)
    assert str(e.value) == 'partition block count must be between 1 and 3'
    for bad in (None, 0, '01', {0}, iter([0])):
        with pytest.raises(TypeError) as e:
            f(W, [bad])
        assert str(e.value) == 'partition blocks must be lists or tuples'
    for blk in ([], [0, 1, 2, 0]):
        with pytest.raises(ValueError) as e:
            f(W, [blk])
        assert str(e.value) == 'partition block length must be between 1 and 3'
    with pytest.raises(ValueError) as e:
        f(W, [[Boom()] * 4])
    assert str(e.value) == 'partition block length must be between 1 and 3'
    for bad in (True, 0.0, '0', None, [0], Boom()):
        with pytest.raises(TypeError) as e:
            f(W, [[bad]])
        assert str(e.value) == 'partition entries must be nonbool int'
    for bad in (3, -1, 10 ** 30):
        with pytest.raises(ValueError) as e:
            f(W, [[bad]])
        assert str(e.value) == 'partition entries must be between 0 and 2'
    with pytest.raises(ValueError) as e:
        f(W, [[0, 1], [1, 2]])
    assert str(e.value) == 'partition entries must be distinct'
    for blocks in ([[0, 1]], [[0], [1]]):
        with pytest.raises(ValueError) as e:
            f(W, blocks)
        assert str(e.value) == 'partition must cover every state'
    with pytest.raises(ValueError) as e:           # W first
        f([[0]], [[9]])
    assert str(e.value) == E_SUM


def test_start_and_k_caps_and_order():
    W = [[1, 1], [1, 2]]
    f = total_variation_to_stationary
    f(W, 1, 64)
    f(W, 0, 0)
    for bad in (2, -1, 10 ** 30):
        with pytest.raises(ValueError) as e:
            f(W, bad, 1)
        assert str(e.value) == 'start must be between 0 and 1'
    for bad in (65, -1, 10 ** 30):
        with pytest.raises(ValueError) as e:
            f(W, 0, bad)
        assert str(e.value) == 'k must be between 0 and 64'
    for bad in (True, 0.0, '0', None, [0], Boom()):
        with pytest.raises(TypeError) as e:
            f(W, bad, 1)
        assert str(e.value) == 'start must be a nonbool int'
        with pytest.raises(TypeError) as e:
            f(W, 0, bad)
        assert str(e.value) == 'k must be a nonbool int'
    with pytest.raises(ValueError) as e:            # start range before k type? start first, then k
        f(W, 2, 65)
    assert str(e.value) == 'start must be between 0 and 1'
    with pytest.raises(TypeError) as e:
        f(W, True, 65)
    assert str(e.value) == 'start must be a nonbool int'
    with pytest.raises(ValueError) as e:
        f(W, 5, True)
    assert str(e.value) == 'start must be between 0 and 1'
    # W is checked before start; arguments are checked before the ergodicity condition
    with pytest.raises(ValueError) as e:
        f([[0]], 9, 99)
    assert str(e.value) == E_SUM
    with pytest.raises(ValueError) as e:
        f([[1, 0], [0, 1]], 0, 99)
    assert str(e.value) == 'k must be between 0 and 64'
    with pytest.raises(ValueError) as e:
        f([[1, 0], [0, 1]], 0, 1)
    assert str(e.value) == 'chain must be irreducible and aperiodic'
    with pytest.raises(ValueError) as e:
        f([[0, 1], [1, 0]], 0, 1)
    assert str(e.value) == 'chain must be irreducible and aperiodic'


def test_caps_and_docs():
    assert (m.MAX_N, m.MAX_W, m.MAX_K) == (7, 1000, 64)
    assert 'SCOPE' in m.__doc__ and 'NOT_CLAIMED' in m.__doc__
    big = [[1000] * 7 for _ in range(7)]
    assert stationary_distributions(big)['distributions'][0]['distribution'] == [F(1, 7)] * 7
    assert total_variation_to_stationary(big, 3, 64)['tv'] == 0
    assert class_periods([[0, 1, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0],
                          [0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 0, 1],
                          [1, 0, 0, 0, 0, 0, 0]])['periods'] == [{'states': list(range(7)), 'period': 7}]
