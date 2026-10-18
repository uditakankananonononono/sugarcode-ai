import itertools
from fractions import Fraction as F
from math import comb

import pytest

import sugarcode.extra_doc.counting_walks_exact as m
from sugarcode.extra_doc.counting_walks_exact import (
    ballot_count, bounded_walk_distribution, dice_sum_distribution,
    gamblers_ruin_expected_duration, gamblers_ruin_probability, lattice_paths_under_slope,
    ruin_stopping_time_distribution, walk_hit_level_count, walk_max_distribution,
    walk_return_count_distribution)

CL = {'gambling_advice': False, 'real_world_odds': False, 'randomness': False, 'forecast': False}


def o_ballot(a, b):
    return sum(1 for s in itertools.product((1, -1), repeat=a + b) if s.count(1) == a and
               all(sum(s[:i]) >= 0 for i in range(len(s) + 1)))


def o_paths(mm, n, p, q):
    c = 0
    for steps in itertools.combinations(range(mm + n), mm):
        x = y = 0
        ok = True
        for t in range(mm + n):
            if t in steps:
                x += 1
            else:
                y += 1
            if y * q > x * p:
                ok = False
                break
        c += ok
    return c


def o_solve(N, p, win):
    """Gauss elimination on the first-step equations; win=True for probability, else duration."""
    q = 1 - p
    n = N + 1
    A = [[F(0)] * n for _ in range(n)]
    b = [F(0)] * n
    for i in range(n):
        A[i][i] = F(1)
    for i in range(1, N):
        A[i][i + 1] -= p
        A[i][i - 1] -= q
        b[i] = F(0) if win else F(1)
    if win:
        b[N] = F(1)
    M = [A[i] + [b[i]] for i in range(n)]
    for c in range(n):
        piv = next(r for r in range(c, n) if M[r][c])
        M[c], M[piv] = M[piv], M[c]
        M[c] = [x / M[c][c] for x in M[c]]
        for r in range(n):
            if r != c and M[r][c]:
                f = M[r][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] for i in range(n)]


def o_walk_enum(states, start, steps, mode, p):
    q = 1 - p
    out = [F(0)] * states

    def go(pos, k, pr):
        if k == steps:
            out[pos] += pr
            return
        if pos in (0, states - 1):
            if mode == 'absorbing':
                go(pos, k + 1, pr)
            else:
                go(pos + 1 if pos == 0 else pos - 1, k + 1, pr)
        else:
            go(pos + 1, k + 1, pr * p)
            go(pos - 1, k + 1, pr * q)
    go(start, 0, F(1))
    return out


def test_ballot_and_paths():
    for a in range(0, 8):
        for b in range(0, 8):
            if a + b <= 14:
                assert ballot_count(a, b)['count'] == o_ballot(a, b)
    for a in range(0, 31):
        for b in range(0, 31):
            want = (a - b + 1) * comb(a + b, b) // (a + 1) if a >= b else 0
            assert ballot_count(a, b)['count'] == want
    assert ballot_count(3, 3)['count'] == 5 and ballot_count(0, 1)['count'] == 0
    for mm in range(0, 7):
        for n in range(0, 7):
            for p in range(1, 4):
                for q in range(1, 4):
                    assert lattice_paths_under_slope(mm, n, p, q)['count'] == o_paths(mm, n, p, q)
    assert lattice_paths_under_slope(30, 30, 1, 1)['count'] == comb(60, 30) // 31
    assert lattice_paths_under_slope(4, 4, 1, 1)['count'] == 14
    assert lattice_paths_under_slope(0, 0, 5, 5)['count'] == 1


def test_ruin_vs_linear_solve_and_closed_cases():
    for N in (1, 2, 3, 5, 8, 13):
        for pn, pd in ((1, 2), (1, 3), (2, 3), (3, 7), (99, 100), (1, 100)):
            p = F(pn, pd)
            win = o_solve(N, p, True)
            dur = o_solve(N, p, False)
            for i in range(N + 1):
                r = gamblers_ruin_probability(i, N, pn, pd)
                assert r['win'] == win[i] and r['ruin'] == 1 - win[i]
                assert gamblers_ruin_expected_duration(i, N, pn, pd)['duration'] == dur[i]
    assert gamblers_ruin_probability(10, 60, 1, 2)['win'] == F(1, 6)
    assert gamblers_ruin_expected_duration(10, 60, 2, 4)['duration'] == 500
    assert gamblers_ruin_probability(0, 5, 1, 3)['win'] == 0
    assert gamblers_ruin_probability(5, 5, 1, 3)['win'] == 1
    assert gamblers_ruin_expected_duration(0, 5, 1, 3)['duration'] == 0
    w = gamblers_ruin_probability(60, 60, 99, 100)
    assert w['win'] == 1
    gamblers_ruin_probability(30, 60, 99, 100)


def test_walk_vs_enumeration_and_totals():
    for states in (2, 3, 4, 5):
        for start in range(states):
            for steps in range(0, 9):
                for mode in ('absorbing', 'reflecting'):
                    for pn, pd in ((1, 2), (2, 5), (99, 100)):
                        r = bounded_walk_distribution(states, start, steps, mode, pn, pd)
                        assert r['law'] == o_walk_enum(states, start, steps, mode, F(pn, pd))
                        assert sum(r['law']) == 1
    big = bounded_walk_distribution(11, 5, 60, 'absorbing', 1, 2)
    assert sum(big['law']) == 1 and big['law'][0] == big['law'][10]
    r = bounded_walk_distribution(3, 1, 2, 'reflecting', 1, 3)
    assert r['law'] == [F(0), F(1), F(0)]
    assert bounded_walk_distribution(3, 1, 1, 'absorbing', 1, 3)['law'] == [F(2, 3), F(0), F(1, 3)]
    assert bounded_walk_distribution(3, 1, 3, 'absorbing', 1, 3)['law'] == [F(2, 3), F(0), F(1, 3)]
    # walk absorption agrees with the ruin probabilities as steps grow
    lim = bounded_walk_distribution(6, 2, 60, 'absorbing', 1, 2)['law']
    assert 0 < F(2, 5) - lim[5] < F(1, 100) and lim[5] <= F(2, 5)


def test_dice_vs_enumeration():
    for n in range(1, 5):
        for s in range(1, 7):
            cnt = {}
            for o in itertools.product(range(1, s + 1), repeat=n):
                cnt[sum(o)] = cnt.get(sum(o), 0) + 1
            assert dice_sum_distribution(n, s)['totals'] == sorted(cnt.items())
    r = dice_sum_distribution(10, 12)['totals']
    assert sum(c for _, c in r) == 12 ** 10 and r[0] == (10, 1) and r[-1] == (120, 1)
    assert dice_sum_distribution(2, 6)['totals'][5] == (7, 6)
    assert dice_sum_distribution(3, 1)['totals'] == [(3, 1)]


def chk(f, args, exc, msg):
    with pytest.raises(exc) as e:
        f(*args)
    assert str(e.value) == msg


def test_multi_arg_caps_types_and_order():
    for g in (ballot_count,):
        g(30, 30)
        chk(g, (31, 0), ValueError, 'a must be between 0 and 30')
        chk(g, (0, 31), ValueError, 'b must be between 0 and 30')
        chk(g, (-1, 31), ValueError, 'a must be between 0 and 30')
        chk(g, (0, True), TypeError, 'b must be a nonbool int')
        chk(g, (None, 99), TypeError, 'a must be a nonbool int')
    g = lattice_paths_under_slope
    g(30, 30, 5, 5)
    g(0, 0, 1, 1)
    chk(g, (31, 0, 1, 1), ValueError, 'm must be between 0 and 30')
    chk(g, (0, 31, 1, 1), ValueError, 'n must be between 0 and 30')
    chk(g, (0, 0, 0, 1), ValueError, 'p must be between 1 and 5')
    chk(g, (0, 0, 6, 1), ValueError, 'p must be between 1 and 5')
    chk(g, (0, 0, 1, 0), ValueError, 'q must be between 1 and 5')
    chk(g, (0, 0, 1, 6), ValueError, 'q must be between 1 and 5')
    chk(g, (0, 0, True, 1), TypeError, 'p must be a nonbool int')
    chk(g, (0, 0, 1, 2.0), TypeError, 'q must be a nonbool int')
    chk(g, (31, 31, 9, 9), ValueError, 'm must be between 0 and 30')
    chk(g, (0, 0, 0, True), ValueError, 'p must be between 1 and 5')
    chk(g, (0, 0, 9, True), ValueError, 'p must be between 1 and 5')
    h = dice_sum_distribution
    h(10, 12)
    h(1, 1)
    chk(h, (0, 1), ValueError, 'n_dice must be between 1 and 10')
    chk(h, (11, 1), ValueError, 'n_dice must be between 1 and 10')
    chk(h, (1, 0), ValueError, 'sides must be between 1 and 12')
    chk(h, (1, 13), ValueError, 'sides must be between 1 and 12')
    chk(h, (True, 1), TypeError, 'n_dice must be a nonbool int')
    chk(h, (1, None), TypeError, 'sides must be a nonbool int')
    chk(h, (11, 13), ValueError, 'n_dice must be between 1 and 10')


@pytest.mark.parametrize('f', [gamblers_ruin_probability, gamblers_ruin_expected_duration])
def test_ruin_validation(f):
    f(60, 60, 99, 100)
    f(0, 1, 1, 2)
    chk(f, (0, 61, 1, 2), ValueError, 'target must be between 1 and 60')
    chk(f, (0, 0, 1, 2), ValueError, 'target must be between 1 and 60')
    chk(f, (6, 5, 1, 2), ValueError, 'start must be between 0 and 5')
    chk(f, (-1, 5, 1, 2), ValueError, 'start must be between 0 and 5')
    chk(f, (1, 5, 1, 101), ValueError, 'p_den must be between 1 and 100')
    chk(f, (1, 5, 1, 0), ValueError, 'p_den must be between 1 and 100')
    chk(f, (1, 5, 0, 2), ValueError, 'p_num must be between 1 and 1')
    chk(f, (1, 5, 2, 2), ValueError, 'p_num must be between 1 and 1')
    chk(f, (1, 5, 1, 1), ValueError, 'p_num must be between 1 and 0')
    chk(f, (1, 5, 100, 100), ValueError, 'p_num must be between 1 and 99')
    chk(f, (1, True, 1, 2), TypeError, 'target must be a nonbool int')
    chk(f, (True, 5, 1, 2), TypeError, 'start must be a nonbool int')
    chk(f, (1, 5, 1.0, 2), TypeError, 'p_num must be a nonbool int')
    chk(f, (1, 5, 1, True), TypeError, 'p_den must be a nonbool int')
    chk(f, (True, 61, 0, 0), ValueError, 'target must be between 1 and 60')
    chk(f, (9, 5, 0, 0), ValueError, 'start must be between 0 and 5')
    chk(f, (1, 5, True, 0), ValueError, 'p_den must be between 1 and 100')


def test_walk_validation():
    f = bounded_walk_distribution
    f(12, 11, 60, 'reflecting', 99, 100)
    f(2, 0, 0, 'absorbing', 1, 2)
    chk(f, (1, 0, 0, 'absorbing', 1, 2), ValueError, 'states must be between 2 and 12')
    chk(f, (13, 0, 0, 'absorbing', 1, 2), ValueError, 'states must be between 2 and 12')
    chk(f, (5, 5, 0, 'absorbing', 1, 2), ValueError, 'start must be between 0 and 4')
    chk(f, (5, 0, 61, 'absorbing', 1, 2), ValueError, 'steps must be between 0 and 60')
    chk(f, (5, 0, -1, 'absorbing', 1, 2), ValueError, 'steps must be between 0 and 60')
    for bad in (None, b'absorbing', 1, True, ['absorbing']):
        chk(f, (5, 0, 1, bad, 1, 2), TypeError, 'mode must be an exact str')

    class S(str):
        pass

    for bad in ('', 'Absorbing', 'periodic', 'absorbing '):
        chk(f, (5, 0, 1, bad, 1, 2), ValueError, "mode must be 'absorbing' or 'reflecting'")
    chk(f, (5, 0, 1, 'absorbing', 2, 2), ValueError, 'p_num must be between 1 and 1')
    chk(f, (5, 0, 1, 'absorbing', 1, 101), ValueError, 'p_den must be between 1 and 100')
    chk(f, (True, 0, 1, 'x', 1, 2), TypeError, 'states must be a nonbool int')
    chk(f, (5, True, 1, 'x', 1, 2), TypeError, 'start must be a nonbool int')
    chk(f, (5, 0, True, 'x', 1, 2), TypeError, 'steps must be a nonbool int')
    chk(f, (5, 0, 1, 'x', 1, 2), ValueError, "mode must be 'absorbing' or 'reflecting'")
    chk(f, (99, 99, 99, 5, 0, 0), ValueError, 'states must be between 2 and 12')
    chk(f, (5, 0, 1, 5, 0, 0), TypeError, 'mode must be an exact str')
    chk(f, (5, 0, 1, 'x', True, 2), ValueError, "mode must be 'absorbing' or 'reflecting'")


def test_claims_false_and_copied_and_docs():
    rs = [walk_max_distribution(3), walk_return_count_distribution(3), walk_hit_level_count(3, 1),
          ruin_stopping_time_distribution(1, 2, 1, 2, 1), ballot_count(2, 1),
          lattice_paths_under_slope(2, 2, 1, 1), gamblers_ruin_probability(1, 2, 1, 2),
          gamblers_ruin_expected_duration(1, 2, 1, 2),
          bounded_walk_distribution(3, 1, 1, 'absorbing', 1, 2), dice_sum_distribution(1, 2)]
    assert len(rs) == 10
    for r in rs:
        assert r['claims'] == CL and all(v is False for v in r['claims'].values())
        r['claims']['randomness'] = True
    assert m.CLAIMS['randomness'] is False
    assert 'SCOPE' in m.__doc__ and 'NOT_CLAIMED' in m.__doc__


def all_walks(n):
    for st in itertools.product((1, -1), repeat=n):
        pos, path = 0, [0]
        for d in st:
            pos += d
            path.append(pos)
        yield path


def test_walk_statistics_vs_enumeration():
    for n in range(0, 15):
        mx, rt = {}, {}
        for path in all_walks(n):
            mx[max(path)] = mx.get(max(path), 0) + 1
            r = sum(1 for x in path[1:] if x == 0)
            rt[r] = rt.get(r, 0) + 1
        assert walk_max_distribution(n)['maxima'] == sorted(mx.items())
        assert walk_return_count_distribution(n)['returns'] == sorted(rt.items())
        for level in range(1, 17):
            want = sum(1 for path in all_walks(n) if max(path) >= level)
            assert walk_hit_level_count(n, level)['count'] == want, (n, level)


def test_walk_statistics_vs_closed_forms_to_cap():
    for n in range(0, 25):
        r = walk_max_distribution(n)['maxima']
        assert sum(c for _, c in r) == 2 ** n
        # P(max >= h) = P(S_n >= h) + P(S_n > h) (reflection principle), counts of end points
        def ends_ge(h):
            return sum(comb(n, k) for k in range(n + 1) if 2 * k - n >= h)
        for h in range(1, 25):
            want = ends_ge(h) + ends_ge(h + 1)
            assert walk_hit_level_count(n, h)['count'] == want
            assert want == sum(c for mx, c in r if mx >= h)
        # number of walks with max 0 is C(n, n//2); returns total equals sum over time
        assert dict(r).get(0, 0) == comb(n, n // 2)
        rr = walk_return_count_distribution(n)['returns']
        assert sum(c for _, c in rr) == 2 ** n


def test_return_total_matches_time_sum():
    for n in range(0, 25):
        rr = walk_return_count_distribution(n)['returns']
        # E[returns] total over walks = sum over even t of C(t, t/2) * 2^(n-t)
        assert sum(k * c for k, c in rr) == sum(comb(t, t // 2) * 2 ** (n - t) for t in range(2, n + 1, 2))


def o_stop(start, target, p, steps):
    q = 1 - p
    out = [F(0)] * (steps + 1)
    still = [F(0)]

    def go(pos, t, pr):
        if pos in (0, target):
            out[t] += pr
            return
        if t == steps:
            still[0] += pr
            return
        go(pos + 1, t + 1, pr * p)
        go(pos - 1, t + 1, pr * q)
    go(start, 0, F(1))
    return out, still[0]


def test_ruin_stopping_vs_enumeration_and_limit():
    for target in (1, 2, 3, 4, 5):
        for start in range(target + 1):
            for steps in range(0, 9):
                for pn, pd in ((1, 2), (1, 3), (99, 100)):
                    r = ruin_stopping_time_distribution(start, target, pn, pd, steps)
                    want, still = o_stop(start, target, F(pn, pd), steps)
                    assert r['stop_at'] == want and r['still_playing'] == still
                    assert sum(r['stop_at']) + r['still_playing'] == 1
    r = ruin_stopping_time_distribution(5, 10, 1, 2, 60)
    assert 0 < r['still_playing'] < 1
    # the stopping law's mean (truncated) never exceeds the exact expected duration
    mean = sum(t * pr for t, pr in enumerate(r['stop_at']))
    assert mean <= gamblers_ruin_expected_duration(5, 10, 1, 2)['duration'] == 25
    # stopping at time 0 only at the ends
    assert ruin_stopping_time_distribution(0, 3, 1, 2, 2)['stop_at'] == [F(1), F(0), F(0)]
    assert ruin_stopping_time_distribution(2, 4, 1, 2, 0) == {
        'start': 2, 'target': 4, 'steps': 0, 'stop_at': [F(0)], 'still_playing': F(1), 'claims': CL}


def test_new_validation():
    for f, top in ((walk_max_distribution, 24), (walk_return_count_distribution, 24)):
        f(0)
        f(top)
        chk(f, (-1,), ValueError, 'n must be between 0 and 24')
        chk(f, (25,), ValueError, 'n must be between 0 and 24')
        for bad in (True, 1.0, '1', None):
            chk(f, (bad,), TypeError, 'n must be a nonbool int')
    f = walk_hit_level_count
    f(24, 24)
    f(0, 1)
    chk(f, (25, 1), ValueError, 'n must be between 0 and 24')
    chk(f, (0, 0), ValueError, 'level must be between 1 and 24')
    chk(f, (0, 25), ValueError, 'level must be between 1 and 24')
    chk(f, (True, 1), TypeError, 'n must be a nonbool int')
    chk(f, (1, True), TypeError, 'level must be a nonbool int')
    chk(f, (25, 25), ValueError, 'n must be between 0 and 24')
    chk(f, (True, 99), TypeError, 'n must be a nonbool int')
    g = ruin_stopping_time_distribution
    g(20, 20, 99, 100, 60)
    g(0, 1, 1, 2, 0)
    chk(g, (0, 21, 1, 2, 0), ValueError, 'target must be between 1 and 20')
    chk(g, (0, 0, 1, 2, 0), ValueError, 'target must be between 1 and 20')
    chk(g, (6, 5, 1, 2, 0), ValueError, 'start must be between 0 and 5')
    chk(g, (1, 5, 2, 2, 0), ValueError, 'p_num must be between 1 and 1')
    chk(g, (1, 5, 1, 101, 0), ValueError, 'p_den must be between 1 and 100')
    chk(g, (1, 5, 1, 2, 61), ValueError, 'steps must be between 0 and 60')
    chk(g, (1, 5, 1, 2, -1), ValueError, 'steps must be between 0 and 60')
    chk(g, (1, 5, 1, 2, True), TypeError, 'steps must be a nonbool int')
    chk(g, (1, True, 1, 2, 0), TypeError, 'target must be a nonbool int')
    chk(g, (True, 5, 1, 2, 0), TypeError, 'start must be a nonbool int')
    chk(g, (1, 5, 1.0, 2, 0), TypeError, 'p_num must be a nonbool int')
    chk(g, (1, 5, 1, True, 0), TypeError, 'p_den must be a nonbool int')
    chk(g, (1, 5, 9, 2, 99), ValueError, 'p_num must be between 1 and 1')
    chk(g, (9, 5, 1, 2, 99), ValueError, 'start must be between 0 and 5')
    chk(g, (0, 21, 1, 2, True), ValueError, 'target must be between 1 and 20')
