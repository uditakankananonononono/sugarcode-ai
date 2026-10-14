import random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.tension import analyse_tension as at


def test_hand_cases():
    r = at([1, 2, 5, 3, 3, 0])
    assert r == {'climax_scene': 2, 'climax_value': 5, 'build': 4, 'release': 5, 'builds_to_climax': True,
                 'released_after_climax': True, 'release_fraction': 1, 'reversals': 1, 'peaks': [2]}
    # ties: the first maximum is the climax; a dip before it breaks builds_to_climax
    r = at([3, 1, 3, 3])
    assert r['climax_scene'] == 0 and r['builds_to_climax'] is True and r['released_after_climax'] is True
    r = at([1, 3, 2, 4, 4, 1])
    assert r['climax_scene'] == 3 and r['builds_to_climax'] is False and r['reversals'] == 3 and r['peaks'] == [1]   # the 4,4 plateau is not a strict peak
    assert r['build'] == 2 + 2 and r['release'] == 1 + 3 and r['release_fraction'] == F(3, 4)
    # flat curve and all zero
    r = at([0, 0, 0])
    assert r['release_fraction'] == 0 and r['peaks'] == [] and r['reversals'] == 0 and r['climax_scene'] == 0
    # endpoint peaks count
    assert at([5, 1])['peaks'] == [0] and at([1, 5])['peaks'] == [1]
    assert at([F(1, 2), F(3, 2), F(3, 2), F(1, 2)])['peaks'] == []
    # rising to the end: no release
    r = at([1, 2, 3])
    assert r['released_after_climax'] is False and r['release_fraction'] == 0 and r['release'] == 0


def test_independent_oracle():
    rnd = random.Random(41)
    for _ in range(500):
        n = rnd.randint(2, 12)
        t = [F(rnd.randint(0, 6), rnd.randint(1, 2)) for _ in range(n)]
        r = at(t)
        top = max(t)
        assert r['climax_scene'] == t.index(top) and r['climax_value'] == top
        assert r['build'] == sum(max(t[i + 1] - t[i], 0) for i in range(n - 1))
        assert r['release'] == sum(max(t[i] - t[i + 1], 0) for i in range(n - 1))
        assert t[0] + r['build'] - r['release'] == t[-1]
        c = t.index(top)
        assert r['builds_to_climax'] == all(t[i] <= t[i + 1] for i in range(c))
        assert r['released_after_climax'] == any(t[i] > t[i + 1] for i in range(c, n - 1))
        assert r['release_fraction'] == (F(0) if top == 0 else (top - t[-1]) / top)
        # peaks by neighbour definition; reversals by run-length on the sign string
        pk = [i for i in range(n) if all(t[i] > t[j] for j in (i - 1, i + 1) if 0 <= j < n)]
        assert r['peaks'] == pk
        s = ''.join('u' if t[i + 1] > t[i] else 'd' for i in range(n - 1) if t[i + 1] != t[i])
        assert r['reversals'] == sum(1 for i in range(len(s) - 1) if s[i] != s[i + 1])


def test_boundaries_and_caps():
    big = 2 ** 32 - 1
    assert at([big, 0]) and at([0, F(1, big)]) and at([0] * 32)
    assert at([F(big, big - 2), 0])
    for bad in (2 ** 32, F(1, 2 ** 32), F(2 ** 32, 3)):
        with pytest.raises(ValueError, match='^rational values must fit 32 bits$'):
            at([0, bad])


@pytest.mark.parametrize('levels,err,msg', [
    ('xx', TypeError, 'levels must be a list or tuple'),
    (5, TypeError, 'levels must be a list or tuple'),
    ([1], ValueError, 'scene count must be between 2 and 32'),
    ([0] * 33, ValueError, 'scene count must be between 2 and 32'),
    ([1, True], TypeError, 'values must be nonbool int or Fraction'),
    ([1, 0.5], TypeError, 'values must be nonbool int or Fraction'),
    ([1, -1], ValueError, 'levels must be non negative'),
    ([-F(1, 2), 1], ValueError, 'levels must be non negative'),
])
def test_exact_errors(levels, err, msg):
    with pytest.raises(err, match='^' + msg + '$'):
        at(levels)


def test_one_negative_level_in_every_position():
    for pos in range(4):
        t = [1, 1, 1, 1]
        t[pos] = -1
        with pytest.raises(ValueError, match='^levels must be non negative$'):
            at(t)
