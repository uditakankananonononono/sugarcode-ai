"""Row 375 tests: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc.pmf_assessment import ANSWERS, assess_fit as af


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


def refuses(error, msg, a):
    with pytest.raises(error) as e:
        af(a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'responses must be a list or tuple'
CNT = 'response count must be between 1 and 200'
ANS = 'responses must be very_disappointed, somewhat_disappointed or not_disappointed'
V, S_, N = ANSWERS


def test_answers():
    assert ANSWERS == ('very_disappointed', 'somewhat_disappointed', 'not_disappointed')


def test_threshold_literals():
    r = af([V, V, S_, N, N])
    assert r == {'counts': {V: 2, S_: 1, N: 2}, 'total': 5, 'very_disappointed_share': F(2, 5),
                 'meets_two_fifths': True, 'fit_validated': False}
    r = af([V, S_, N, N, N])
    assert r['very_disappointed_share'] == F(1, 5) and r['meets_two_fifths'] is False
    assert af([V] * 39 + [N] * 61)['meets_two_fifths'] is False                  # 39/100
    assert af([V] * 40 + [N] * 60)['meets_two_fifths'] is True                   # 40/100
    assert af([V] * 41 + [N] * 59)['meets_two_fifths'] is True
    assert af([V])['meets_two_fifths'] is True and af([N])['meets_two_fifths'] is False
    assert af([S_] * 3)['counts'] == {V: 0, S_: 3, N: 0}
    assert af((V, N))['very_disappointed_share'] == F(1, 2)


def test_caps_n_and_n_plus_1():
    assert af([V] * 200)['total'] == 200
    refuses(ValueError, CNT, [V] * 201)
    refuses(ValueError, CNT, [])
    refuses(ValueError, ANS, [V, 'x'])
    refuses(ValueError, ANS, ['x', V])
    refuses(ValueError, ANS, [''])
    refuses(ValueError, ANS, ['Very_disappointed'])
    refuses(ValueError, ANS, ['very_disappointed '])
    for ch in ('\x00', '\n', '\u200b', '\ue000', '\ud800', '\u0378', '\u00e9'):
        refuses(ValueError, ANS, [V + ch])
        refuses(ValueError, ANS, [V, ch])


def test_exact_types():
    refuses(TypeError, TY, L([V]))
    refuses(TypeError, TY, T((V,)))
    for b in (None, 'abc', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b)
    for b in (S(V), 1, None, b'x', True, ['very_disappointed']):
        refuses(ValueError, ANS, [b])
        refuses(ValueError, ANS, [V, b])
    src = [V]
    r = af(src)
    r['counts'][V] = 9
    assert src == [V]


def test_check_order():
    refuses(TypeError, TY, 1)
    refuses(ValueError, CNT, [])
    refuses(ValueError, ANS, [5] * 3)
