import random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.kaizen_tracker import improvement_trend as trend, cycles_to_target as ctt


def oracle_trend(ys):
    n = len(ys)
    xm = F(n - 1, 2)
    ym = sum(ys) / n
    sxx = sum((i - xm) ** 2 for i in range(n))
    slope = sum((i - xm) * (y - ym) for i, y in enumerate(ys)) / sxx
    return slope, ym - slope * xm


def longest_down(ys):
    best = cur = 0
    for i in range(1, len(ys)):
        cur = cur + 1 if ys[i] < ys[i - 1] else 0
        best = max(best, cur)
    return best


def test_trend_vs_oracle_random():
    rnd = random.Random(18)
    for _ in range(500):
        ys = [F(rnd.randint(0, 40), rnd.randint(1, 4)) for _ in range(rnd.randint(2, 15))]
        r = trend(ys)
        s, b = oracle_trend(ys)
        assert r['slope'] == s and r['intercept'] == b
        assert r['steps_improving'] == sum(1 for i in range(1, len(ys)) if ys[i] < ys[i - 1])
        assert r['longest_improving_streak'] == longest_down(ys)
        assert r['total_change'] == ys[-1] - ys[0]
        assert r['relative_reduction'] == (None if ys[0] == 0 else (ys[0] - ys[-1]) / ys[0])
        assert r['improving'] == (s < 0)


def test_trend_hand_cases():
    r = trend([10, 8, 6, 4])
    assert r['slope'] == -2 and r['intercept'] == 10 and r['steps_improving'] == 3 and r['longest_improving_streak'] == 3
    assert r['total_change'] == -6 and r['relative_reduction'] == F(3, 5) and r['improving'] is True
    r = trend([5, 5, 5])
    assert r['slope'] == 0 and r['improving'] is False and r['steps_improving'] == 0 and r['relative_reduction'] == 0
    r = trend([4, 3, 5, 4, 3, 2, 6])
    assert r['steps_improving'] == 4 and r['longest_improving_streak'] == 3 and r['total_change'] == 2
    assert r['relative_reduction'] == F(-1, 2)
    assert trend([0, 3])['relative_reduction'] is None and trend((1, 2))['slope'] == 1
    assert trend([3, 3, 2])['longest_improving_streak'] == 1


def oracle_cycles(cur, tgt, r):
    cur, tgt, r = F(cur), F(tgt), F(r)
    a, b = (1 - r).numerator, (1 - r).denominator
    for n in range(201):
        if cur.numerator * a ** n * tgt.denominator * b ** 0 * 1 <= tgt.numerator * cur.denominator * b ** n:
            return n
    return None


def test_cycles_vs_integer_oracle():
    rnd = random.Random(19)
    for _ in range(500):
        cur = F(rnd.randint(0, 200), rnd.randint(1, 5))
        tgt = F(rnd.randint(0, 100), rnd.randint(1, 5))
        r = F(rnd.randint(1, 9), 10) if rnd.random() < .8 else F(rnd.randint(1, 49), 50)
        o = oracle_cycles(cur, tgt, r)
        res = ctt(cur, tgt, r)
        assert res['cycles'] == o and res['reachable'] == (o is not None)
        if o is not None:
            assert res['value_after'] == cur * (1 - r) ** o and res['value_after'] <= tgt
            assert o == 0 or cur * (1 - r) ** (o - 1) > tgt


def test_cycles_hand_cases():
    assert ctt(100, 50, F(1, 2)) == {'cycles': 1, 'value_after': 50, 'reachable': True}
    assert ctt(100, 51, F(1, 2))['cycles'] == 1 and ctt(100, 49, F(1, 2))['cycles'] == 2
    assert ctt(10, 10, F(1, 10))['cycles'] == 0 and ctt(5, 10, F(1, 10))['value_after'] == 5
    assert ctt(0, 0, F(1, 10))['cycles'] == 0
    r = ctt(1, 0, F(1, 2))
    assert r == {'cycles': None, 'value_after': None, 'reachable': False}
    assert ctt(1000000, 1, F(1, 2))['cycles'] == 20
    # exactly 200 cycles is allowed, 201 is not (1e6 * 0.9 ** 200 sits between 1/1418 and 1/1417)
    r = ctt(10 ** 6, F(1, 1417), F(1, 10))
    assert r['cycles'] == 200 and r['reachable'] is True and r['value_after'] <= F(1, 1417)
    assert r['value_after'] == 10 ** 6 * F(9, 10) ** 200 and 10 ** 6 * F(9, 10) ** 199 > F(1, 1417)
    assert ctt(10 ** 6, F(1, 1418), F(1, 10)) == {'cycles': None, 'value_after': None, 'reachable': False}
    assert 10 ** 6 * F(9, 10) ** 200 > F(1, 1418)


def test_caps_accept():
    trend([1000000] * 60)
    trend([0, 0])
    trend([F(1, 2 ** 32 - 1), 1])
    trend([F(2 ** 31 + 1, 2 ** 31 + 3), 1])
    ctt(1000000, 0, F(1, 2 ** 32 - 1))
    ctt(0, 0, F(2 ** 32 - 2, 2 ** 32 - 1))
    ctt(1, 1, F(2 ** 31 + 1, 2 ** 31 + 3))


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


T, V = TypeError, ValueError


def test_pins_trend():
    err(trend, T, 'values must be a list or tuple', 'ab')
    err(trend, V, 'value count must be between 2 and 60', [1])
    err(trend, V, 'value count must be between 2 and 60', [1] * 61)
    for bad in (True, 1.0, '1', None):
        err(trend, T, 'value must be a nonbool int or Fraction', [1, bad])
    err(trend, V, 'rational values must fit 32 bits', [1, F(1, 2 ** 32)])
    err(trend, V, 'rational values must fit 32 bits', [1, F(2 ** 32 + 1, 2 ** 32 + 3)])
    err(trend, V, 'value must be between 0 and 1000000', [1, -1])
    err(trend, V, 'value must be between 0 and 1000000', [1, 1000001])
    for pos in range(3):
        v = [1, 1, 1]
        v[pos] = 2.5
        err(trend, T, 'value must be a nonbool int or Fraction', v)


def test_pins_cycles():
    for i, nm in enumerate(('current', 'target', 'reduction')):
        for bad in (True, 1.0, '1', None):
            a = [1, 1, F(1, 2)]
            a[i] = bad
            err(ctt, T, nm + ' must be a nonbool int or Fraction', *a)
    err(ctt, V, 'current must be between 0 and 1000000', -1, 1, F(1, 2))
    err(ctt, V, 'current must be between 0 and 1000000', 1000001, 1, F(1, 2))
    err(ctt, V, 'target must be between 0 and 1000000', 1, -1, F(1, 2))
    err(ctt, V, 'target must be between 0 and 1000000', 1, 1000001, F(1, 2))
    err(ctt, V, 'reduction must be between 0 and 1, exclusive', 1, 1, 0)
    err(ctt, V, 'reduction must be between 0 and 1, exclusive', 1, 1, 1)
    err(ctt, V, 'reduction must be between 0 and 1, exclusive', 1, 1, F(-1, 2))
    err(ctt, V, 'reduction must be between 0 and 1, exclusive', 1, 1, F(3, 2))
    err(ctt, V, 'rational values must fit 32 bits', F(1, 2 ** 32), 1, F(1, 2))
    err(ctt, V, 'rational values must fit 32 bits', 1, F(1, 2 ** 32), F(1, 2))
    err(ctt, V, 'rational values must fit 32 bits', 1, 1, F(1, 2 ** 32))
    err(ctt, V, 'rational values must fit 32 bits', 1, 1, F(2 ** 32 + 1, 2 ** 32 + 3))


def test_numerator_alone_33_bits_refused_first():
    m = 'rational values must fit 32 bits'
    err(trend, V, m, [1, 2 ** 32])
    err(ctt, V, m, 2 ** 32, 1, F(1, 2))
    err(ctt, V, m, 1, 2 ** 32, F(1, 2))
    err(ctt, V, m, 1, 1, F(2 ** 32, 3))
