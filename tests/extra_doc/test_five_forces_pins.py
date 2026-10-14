"""Row 362 tests-only hardening: exact oracle, bounds at N and N+1, exact messages, exact-type pins, check order."""
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc.five_forces import industry_attractiveness as ia, FORCES


class L(list):
    pass


class T(tuple):
    pass


class I(int):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        ia(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'inputs must be lists or tuples'
FIVE = 'exactly five pressures and weights required'
PR = 'pressures must be nonbool integers zero through 100'
WT = 'weights must be nonbool integers zero through 1000'
WZ = 'at least one weight must be positive'


def test_forces_order_literal():
    assert FORCES == ('rivalry', 'entrants', 'substitutes', 'suppliers', 'buyers')


@pytest.mark.parametrize('p,w', [
    ([10, 20, 30, 40, 50], [1, 1, 1, 1, 1]),
    ([100, 0, 0, 0, 0], [1, 0, 0, 0, 0]),
    ([100] * 5, [1000] * 5),
    ([0] * 5, [1, 2, 3, 4, 5]),
    ([33, 66, 99, 1, 2], [3, 7, 11, 13, 17]),
    ([50, 50, 50, 50, 50], [0, 0, 0, 0, 1]),
])
def test_exact_oracle(p, w):
    tot = sum(w)
    contrib = [F(a * b, tot) for a, b in zip(p, w)]
    r = ia(p, w)
    assert r['forces'] == [{'force': n, 'pressure': a, 'contribution': c} for n, a, c in zip(FORCES, p, contrib)]
    assert r['weighted_pressure'] == F(sum(a * b for a, b in zip(p, w)), tot)
    assert r['attractiveness'] == 100 - r['weighted_pressure'] and r['assessment_validated'] is False
    assert all(type(c['contribution']) is F for c in r['forces']) and type(r['weighted_pressure']) is F
    assert set(r) == {'forces', 'weighted_pressure', 'attractiveness', 'assessment_validated'}


def test_literals():
    r = ia([10, 20, 30, 40, 50], [1, 1, 1, 1, 1])
    assert r['weighted_pressure'] == 30 and r['attractiveness'] == 70
    assert r['forces'][0] == {'force': 'rivalry', 'pressure': 10, 'contribution': 2}
    assert r['forces'][4] == {'force': 'buyers', 'pressure': 50, 'contribution': 10}
    r = ia([100, 0, 0, 0, 0], [1, 1, 1, 0, 0])
    assert r['weighted_pressure'] == F(100, 3) and r['attractiveness'] == F(200, 3)
    assert ia([100] * 5, [1000] * 5)['attractiveness'] == 0 and ia([0] * 5, [1] * 5)['attractiveness'] == 100
    assert ia((10,) * 5, (1,) * 5) == ia([10] * 5, [1] * 5)


def test_counts_bounds_n_and_n_plus_1():
    for n in (0, 4, 6):
        refuses(ValueError, FIVE, [1] * n, [1] * 5)
        refuses(ValueError, FIVE, [1] * 5, [1] * n)
    for b in (-1, 101):
        for pos in range(5):
            p = [1] * 5
            p[pos] = b
            refuses(ValueError, PR, p, [1] * 5)
    for b in (-1, 1001):
        for pos in range(5):
            w = [1] * 5
            w[pos] = b
            refuses(ValueError, WT, [1] * 5, w)
    refuses(ValueError, WZ, [1] * 5, [0] * 5)
    assert ia([1] * 5, [0, 0, 0, 0, 1])['weighted_pressure'] == 1


def test_exact_types():
    refuses(TypeError, TY, L([1] * 5), [1] * 5)
    refuses(TypeError, TY, T((1,) * 5), [1] * 5)
    refuses(TypeError, TY, [1] * 5, L([1] * 5))
    refuses(TypeError, TY, [1] * 5, T((1,) * 5))
    for b in (None, 'abcde', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b, [1] * 5)
        refuses(TypeError, TY, [1] * 5, b)
    for b in (True, False, 1.0, I(1), '1', None, F(1)):
        for pos in range(5):
            p = [1] * 5
            p[pos] = b
            refuses(ValueError, PR, p, [1] * 5)
            refuses(ValueError, WT, [1] * 5, p)


def test_check_order():
    refuses(TypeError, TY, 1, 2)
    refuses(ValueError, FIVE, [True], [True])
    refuses(ValueError, PR, [True] * 5, [True] * 5)
    refuses(ValueError, WT, [1] * 5, [True] * 5)
    refuses(ValueError, WZ, [1] * 5, [0] * 5)
