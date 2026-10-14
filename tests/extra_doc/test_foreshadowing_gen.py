import random
from fractions import Fraction as F
from itertools import combinations
import pytest
from sugarcode.extra_doc.foreshadowing_gen import generate_hint_plan as gen


def _notice(sals):
    miss = F(1)
    for s in sals:
        miss *= 1 - s
    return 1 - miss


def _best_positions(reveal, m):
    # brute force over every placement: least longest gap, then largest shortest gap, then smallest positions
    best = None
    for pos in combinations(range(1, reveal), m):
        marks = [0] + list(pos) + [reveal]
        gaps = [b - a for a, b in zip(marks, marks[1:])]
        key = (max(gaps), -min(gaps), list(pos))
        if best is None or key < best:
            best = key
    return best


def _brute(reveal, pool, ms, mn, G):
    best = None
    for mask in range(1 << len(pool)):
        idx = [i for i in range(len(pool)) if mask >> i & 1]
        sal = [pool[i] for i in idx]
        if any(s > ms for s in sal) or len(idx) > reveal - 1 or _notice(sal) < mn:
            continue
        bp = _best_positions(reveal, len(idx))
        if bp is None or bp[0] > G:
            continue
        key = (max(sal, default=F(0)), len(idx), _notice(sal), idx)
        if best is None or key < best[0]:
            best = (key, bp[2])
    return best


def test_hand_cases():
    r = gen(10, 8, [F(1, 4), F(1, 4), F(1, 8)], F(1, 4), F(1, 4), 4)
    assert r['feasible'] and r['chosen'] == [0] and r['hints'] == [(4, F(1, 4))]
    assert r['check'] == {'valid': True, 'late_hints': [], 'notice_probability': F(1, 4), 'subtle': True, 'gaps': [4, 4]}
    # a tighter gap forces more hints: gap 3 over 8 scenes needs 2 hints (ceil(8/3) - 1); gaps 2,3,3 (longer last)
    r = gen(10, 8, [F(1, 8)] * 3, F(1, 4), 0, 3)
    assert r['chosen'] == [0, 1] and [h[0] for h in r['hints']] == [2, 5] and r['check']['gaps'] == [2, 3, 3]
    # nothing needed
    r = gen(5, 5, [F(1, 2)], 1, 0, 5)
    assert r['chosen'] == [] and r['hints'] == [] and r['check']['gaps'] == [5]
    # too loud for the cap: infeasible, with the certificate number
    r = gen(5, 5, [F(1, 2)], F(1, 4), F(1, 10), 5)
    assert r['feasible'] is False and r['max_notice_within_cap'] == 0 and r['hints'] is None
    # notice target out of reach of the quiet hints
    r = gen(10, 8, [F(1, 10)] * 2, F(1, 10), F(1, 2), 8)
    assert r['feasible'] is False and r['max_notice_within_cap'] == F(19, 100)
    # reveal in scene 1 leaves no room for hints
    r = gen(5, 1, [F(1, 2)], 1, F(1, 4), 1)
    assert r['feasible'] is False


def test_independent_oracle_bruteforce():
    rnd = random.Random(61)
    for _ in range(250):
        n = rnd.randint(1, 10)
        reveal = rnd.randint(1, n)
        pool = [F(rnd.randint(1, 8), 8) for _ in range(rnd.randint(0, 5))]
        ms, mn = F(rnd.randint(0, 8), 8), F(rnd.randint(0, 8), 8)
        G = rnd.randint(1, n)
        r = gen(n, reveal, pool, ms, mn, G)
        b = _brute(reveal, pool, ms, mn, G)
        assert r['feasible'] == (b is not None)
        assert r['examined'] == 2 ** len(pool)
        if b is not None:
            assert r['chosen'] == b[0][3]
            assert [h[0] for h in r['hints']] == b[1]
            assert [h[1] for h in r['hints']] == [pool[i] for i in r['chosen']]
            assert r['check']['valid'] and r['check']['subtle'] and max(r['check']['gaps']) <= G


def test_boundaries_and_caps():
    big = 2 ** 32 - 1
    assert gen(64, 64, [F(1, big)] * 8, 1, 0, 64)['feasible']
    assert gen(1, 1, [], 0, 0, 1)['feasible']
    r = gen(64, 64, [F(1, 2)] * 8, F(1, 2), F(1, 2), 8)
    assert r['feasible'] and r['chosen'] == list(range(7))          # ceil(64 / (m + 1)) <= 8 needs m >= 7
    for bad in (2 ** 32, F(1, 2 ** 32), F(2 ** 32, 2 ** 32 + 1)):
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            gen(5, 5, [bad], 1, 0, 5)
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            gen(5, 5, [], bad, 0, 5)
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            gen(5, 5, [], 1, bad, 5)


@pytest.mark.parametrize('args,err,msg', [
    ((True, 1, [], 0, 0, 1), TypeError, 'n_scenes, reveal and max_gap must be nonbool ints'),
    ((5, True, [], 0, 0, 1), TypeError, 'n_scenes, reveal and max_gap must be nonbool ints'),
    ((5, 5, [], 0, 0, True), TypeError, 'n_scenes, reveal and max_gap must be nonbool ints'),
    ((0, 1, [], 0, 0, 1), ValueError, 'n_scenes must be between 1 and 64'),
    ((65, 1, [], 0, 0, 1), ValueError, 'n_scenes must be between 1 and 64'),
    ((5, 0, [], 0, 0, 1), ValueError, 'reveal must be between 1 and n_scenes'),
    ((5, 6, [], 0, 0, 1), ValueError, 'reveal must be between 1 and n_scenes'),
    ((5, 5, [], 0, 0, 0), ValueError, 'max_gap must be between 1 and n_scenes'),
    ((5, 5, [], 0, 0, 6), ValueError, 'max_gap must be between 1 and n_scenes'),
    ((5, 5, 'x', 0, 0, 1), TypeError, 'pool must be a list or tuple of saliences'),
    ((5, 5, [F(1, 2)] * 9, 0, 0, 1), ValueError, 'at most 8 pool hints'),
    ((5, 5, [True], 0, 0, 1), TypeError, 'values must be nonbool int or Fraction'),
    ((5, 5, [0], 0, 0, 1), ValueError, r'salience must be in \(0, 1\]'),
    ((5, 5, [2], 0, 0, 1), ValueError, r'salience must be in \(0, 1\]'),
    ((5, 5, [], -1, 0, 1), ValueError, r'thresholds must be in \[0, 1\]'),
    ((5, 5, [], 2, 0, 1), ValueError, r'thresholds must be in \[0, 1\]'),
    ((5, 5, [], 0, -1, 1), ValueError, r'thresholds must be in \[0, 1\]'),
    ((5, 5, [], 0, 2, 1), ValueError, r'thresholds must be in \[0, 1\]'),
])
def test_exact_errors(args, err, msg):
    with pytest.raises(err, match='^' + msg + '$'):
        gen(*args)


def test_one_bad_salience_in_every_position():
    for pos in range(3):
        pool = [F(1, 2)] * 3
        pool[pos] = F(0)
        with pytest.raises(ValueError, match=r'^salience must be in \(0, 1\]$'):
            gen(5, 5, pool, 1, 0, 5)


def test_validation_runs_even_when_the_answer_is_infeasible():
    # reveal 1 leaves no room for hints, so the v1 checker is never called; own range checks must still fire
    for bad in (F(-1, 2), -1, F(3, 2), 2):
        with pytest.raises(ValueError, match=r'^thresholds must be in \[0, 1\]$'):
            gen(5, 1, [], bad, 1, 1)
        with pytest.raises(ValueError, match=r'^thresholds must be in \[0, 1\]$'):
            gen(5, 1, [], 1, bad, 1)
    for bad in (0, F(-1, 2), 2, F(3, 2)):
        with pytest.raises(ValueError, match=r'^salience must be in \(0, 1\]$'):
            gen(5, 1, [bad], 1, 1, 1)
    assert gen(5, 1, [1], 1, 1, 1)['feasible'] is False
    assert gen(5, 1, [1], 0, 0, 1)['feasible'] is True
