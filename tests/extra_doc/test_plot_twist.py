import random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.plot_twist import design_twist as dt


def test_hand_cases():
    # prior 1/10, two clues each 4x likelier under the twist: BF 16, odds 1/9*16 = 16/9, posterior 16/25
    r = dt(F(1, 10), [(F(1, 2), F(1, 8)), (F(1, 2), F(1, 8))], F(3, 4), F(1, 2))
    assert r == {'surprise': F(9, 10), 'bayes_factor': 16, 'posterior': F(16, 25), 'surprising': True, 'plausible': True, 'well_designed': True}
    # no clues: posterior equals the prior, bayes factor 1
    r = dt(F(1, 4), [], F(1, 2), F(1, 2))
    assert r['posterior'] == F(1, 4) and r['bayes_factor'] == 1 and r['plausible'] is False and r['surprising'] is True
    # uninformative clues do not change belief
    assert dt(F(1, 3), [(F(1, 2), F(1, 2))] * 3, 0, 0)['posterior'] == F(1, 3)
    # expected twist: not surprising
    r = dt(F(9, 10), [(1, F(1, 2))], F(1, 2), F(1, 2))
    assert r['surprising'] is False and r['plausible'] is True and r['well_designed'] is False


def test_independent_oracle_odds_form():
    rnd = random.Random(31)
    for _ in range(400):
        pi = F(rnd.randint(1, 9), 10)
        k = rnd.randint(0, 8)
        cl = [(F(rnd.randint(1, 8), 8), F(rnd.randint(1, 8), 8)) for _ in range(k)]
        ms, mp = F(rnd.randint(0, 10), 10), F(rnd.randint(0, 10), 10)
        r = dt(pi, cl, ms, mp)
        bf = F(1)
        for a, b in cl:
            bf *= a / b
        odds = pi / (1 - pi) * bf
        assert r['bayes_factor'] == bf and r['posterior'] == odds / (1 + odds)
        assert r['surprise'] == 1 - pi
        assert r['surprising'] == (1 - pi >= ms) and r['plausible'] == (odds / (1 + odds) >= mp)
        assert r['well_designed'] == (r['surprising'] and r['plausible'])


def test_threshold_edges_are_inclusive():
    r = dt(F(1, 2), [], F(1, 2), F(1, 2))
    assert r['surprising'] is True and r['plausible'] is True
    r = dt(F(1, 2), [], F(501, 1000), F(501, 1000))
    assert r['surprising'] is False and r['plausible'] is False


def test_boundaries_and_caps():
    big = 2 ** 32 - 1
    assert dt(F(1, big), [], 0, 0) and dt(F(big - 1, big), [], 0, 0)
    assert dt(F(1, 2), [(1, 1)] * 8, 0, 1)
    for bad in (2 ** 32, F(1, 2 ** 32), F(2 ** 32, 2 ** 32 + 1)):
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            dt(bad, [], 0, 0)
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            dt(F(1, 2), [(bad, 1)], 0, 0)
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            dt(F(1, 2), [(1, bad)], 0, 0)
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            dt(F(1, 2), [], bad, 0)
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            dt(F(1, 2), [], 0, bad)


@pytest.mark.parametrize('args,err,msg', [
    ((F(1, 2), 'x', 0, 0), TypeError, 'clues must be a list or tuple of pairs'),
    ((F(1, 2), 5, 0, 0), TypeError, 'clues must be a list or tuple of pairs'),
    ((F(1, 2), [(1, 1)] * 9, 0, 0), ValueError, 'at most 8 clues'),
    ((F(1, 2), [1], 0, 0), TypeError, r'each clue must be a pair \(a, b\)'),
    ((F(1, 2), [(1, 1, 1)], 0, 0), TypeError, r'each clue must be a pair \(a, b\)'),
    ((True, [], 0, 0), TypeError, 'values must be nonbool int or Fraction'),
    ((F(1, 2), [(0.5, 1)], 0, 0), TypeError, 'values must be nonbool int or Fraction'),
    ((0, [], 0, 0), ValueError, r'prior must be in \(0, 1\)'),
    ((1, [], 0, 0), ValueError, r'prior must be in \(0, 1\)'),
    ((F(1, 2), [(0, 1)], 0, 0), ValueError, r'clue probabilities must be in \(0, 1\]'),
    ((F(1, 2), [(1, 0)], 0, 0), ValueError, r'clue probabilities must be in \(0, 1\]'),
    ((F(1, 2), [(2, 1)], 0, 0), ValueError, r'clue probabilities must be in \(0, 1\]'),
    ((F(1, 2), [(1, F(3, 2))], 0, 0), ValueError, r'clue probabilities must be in \(0, 1\]'),
    ((F(1, 2), [], -1, 0), ValueError, r'thresholds must be in \[0, 1\]'),
    ((F(1, 2), [], 2, 0), ValueError, r'thresholds must be in \[0, 1\]'),
    ((F(1, 2), [], 0, -1), ValueError, r'thresholds must be in \[0, 1\]'),
    ((F(1, 2), [], 0, 2), ValueError, r'thresholds must be in \[0, 1\]'),
])
def test_exact_errors(args, err, msg):
    with pytest.raises(err, match='^' + msg + '$'):
        dt(*args)


def test_one_bad_clue_probability_in_every_position():
    for pos in range(4):
        flat = [F(1, 2)] * 4
        flat[pos] = F(0) if pos % 2 else F(3, 2)
        with pytest.raises(ValueError, match=r'^clue probabilities must be in \(0, 1\]$'):
            dt(F(1, 2), [flat[:2], flat[2:]], 0, 0)
