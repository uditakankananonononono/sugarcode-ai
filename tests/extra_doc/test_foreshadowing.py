import random
from fractions import Fraction as F
from itertools import combinations
import pytest
from sugarcode.extra_doc.foreshadowing import place_hints as ph


def test_hand_cases():
    r = ph(10, 8, [(2, F(1, 4)), (5, F(1, 4))], F(1, 2), F(1, 4))
    assert r == {'valid': True, 'late_hints': [], 'notice_probability': F(7, 16), 'subtle': True, 'gaps': [2, 3, 3]}
    # hint at the reveal scene or after is late
    r = ph(10, 5, [(5, F(1, 2)), (9, F(1, 2)), (1, F(1, 2))], 1, 0)
    assert r['valid'] is False and r['late_hints'] == [0, 1]
    # no hints: notice 0, one gap from scene 0 to the reveal
    r = ph(6, 6, [], 1, 0)
    assert r['notice_probability'] == 0 and r['gaps'] == [6] and r['subtle'] is True
    r = ph(6, 6, [], 1, F(1, 100))
    assert r['subtle'] is False
    # a loud hint is not subtle
    assert ph(10, 8, [(2, F(3, 4))], F(1, 2), 0)['subtle'] is False
    # hints are sorted for gaps
    assert ph(10, 9, [(6, F(1, 4)), (3, F(1, 4))], 1, 0)['gaps'] == [3, 3, 3]


def test_independent_oracle_inclusion_exclusion():
    rnd = random.Random(17)
    for _ in range(300):
        n = rnd.randint(1, 20)
        reveal = rnd.randint(1, n)
        k = rnd.randint(0, 6)
        hints = [(rnd.randint(1, n), F(rnd.randint(1, 8), 8)) for _ in range(k)]
        ms, mn = F(rnd.randint(0, 8), 8), F(rnd.randint(0, 8), 8)
        r = ph(n, reveal, hints, ms, mn)
        # P(at least one noticed) by inclusion-exclusion over subsets
        p = F(0)
        for size in range(1, k + 1):
            for sub in combinations(range(k), size):
                term = F(1)
                for i in sub:
                    term *= hints[i][1]
                p += (-1) ** (size + 1) * term
        assert r['notice_probability'] == p
        assert r['late_hints'] == [i for i, h in enumerate(hints) if h[0] >= reveal]
        assert r['valid'] == (not r['late_hints'])
        pts = [0] + sorted(h[0] for h in hints) + [reveal]
        assert r['gaps'] == [b - a for a, b in zip(pts, pts[1:])]
        assert r['subtle'] == (all(h[1] <= ms for h in hints) and p >= mn)


def test_boundaries_and_caps():
    big = 2 ** 32 - 1
    assert ph(64, 64, [(1, F(1, big))] * 8, 1, 0) and ph(1, 1, [], 0, 0)
    assert ph(1, 1, [(1, F(big - 1, big))], 1, 0)['late_hints'] == [0]
    for bad in (2 ** 32, F(1, 2 ** 32), F(2 ** 32, 2 ** 32 + 1)):
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            ph(5, 5, [(1, bad)], 1, 0)
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            ph(5, 5, [], bad, 0)
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            ph(5, 5, [], 1, bad)
    # salience exactly 1 is allowed; the edge of reveal == n_scenes too
    assert ph(5, 5, [(4, 1)], 1, 1)['notice_probability'] == 1


@pytest.mark.parametrize('args,err,msg', [
    ((True, 1, [], 0, 0), TypeError, 'n_scenes and reveal must be nonbool ints'),
    ((5, True, [], 0, 0), TypeError, 'n_scenes and reveal must be nonbool ints'),
    ((0, 1, [], 0, 0), ValueError, 'n_scenes must be between 1 and 64'),
    ((65, 1, [], 0, 0), ValueError, 'n_scenes must be between 1 and 64'),
    ((5, 0, [], 0, 0), ValueError, 'reveal must be between 1 and n_scenes'),
    ((5, 6, [], 0, 0), ValueError, 'reveal must be between 1 and n_scenes'),
    ((5, 5, 'x', 0, 0), TypeError, 'hints must be a list or tuple of pairs'),
    ((5, 5, [(1, 1)] * 9, 0, 0), ValueError, 'at most 8 hints'),
    ((5, 5, [1], 0, 0), TypeError, r'each hint must be a pair \(scene, salience\)'),
    ((5, 5, [(1, 1, 1)], 0, 0), TypeError, r'each hint must be a pair \(scene, salience\)'),
    ((5, 5, [(True, 1)], 0, 0), TypeError, 'hint scenes must be nonbool ints'),
    ((5, 5, [(0, 1)], 0, 0), ValueError, 'hint scene out of range'),
    ((5, 5, [(6, 1)], 0, 0), ValueError, 'hint scene out of range'),
    ((5, 5, [(1, 0.5)], 0, 0), TypeError, 'values must be nonbool int or Fraction'),
    ((5, 5, [(1, 0)], 0, 0), ValueError, r'salience must be in \(0, 1\]'),
    ((5, 5, [(1, 2)], 0, 0), ValueError, r'salience must be in \(0, 1\]'),
    ((5, 5, [], -1, 0), ValueError, r'thresholds must be in \[0, 1\]'),
    ((5, 5, [], 2, 0), ValueError, r'thresholds must be in \[0, 1\]'),
    ((5, 5, [], 0, -1), ValueError, r'thresholds must be in \[0, 1\]'),
    ((5, 5, [], 0, 2), ValueError, r'thresholds must be in \[0, 1\]'),
])
def test_exact_errors(args, err, msg):
    with pytest.raises(err, match='^' + msg + '$'):
        ph(*args)


def test_one_bad_salience_in_every_position():
    for pos in range(3):
        hints = [(1, F(1, 2))] * 3
        hints[pos] = (1, F(0))
        with pytest.raises(ValueError, match=r'^salience must be in \(0, 1\]$'):
            ph(5, 5, hints, 1, 0)
    for pos in range(3):
        hints = [(1, F(1, 2))] * 3
        hints[pos] = (9, F(1, 2))
        with pytest.raises(ValueError, match='^hint scene out of range$'):
            ph(5, 5, hints, 1, 0)
