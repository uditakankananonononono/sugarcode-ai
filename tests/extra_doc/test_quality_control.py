import random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.quality_control import control_chart_signals as ccs, capability as cap


def oracle_rules(xs, c, s):
    out = {'rule1': [], 'rule2': [], 'rule3': [], 'rule4': []}
    for i, x in enumerate(xs):
        if x - c > 3 * s or c - x > 3 * s:
            out['rule1'].append(i)
        for sg in (1, -1):
            def beyond(j, k):
                return sg * (xs[j] - c) > k * s
            w3 = range(max(0, i - 2), i + 1)
            w5 = range(max(0, i - 4), i + 1)
            if beyond(i, 2) and len([j for j in w3 if beyond(j, 2)]) >= 2:
                out['rule2'].append(i)
            if beyond(i, 1) and len([j for j in w5 if beyond(j, 1)]) >= 4:
                out['rule3'].append(i)
        if i >= 7:
            w = xs[i - 7:i + 1]
            if all(v > c for v in w) or all(v < c for v in w):
                out['rule4'].append(i)
    return out


def test_rules_random_vs_oracle():
    rnd = random.Random(16)
    fired = set()
    for _ in range(600):
        n = rnd.randint(1, 20)
        c, s = F(rnd.randint(-5, 5)), F(rnd.randint(1, 4), rnd.randint(1, 3))
        xs = [c + s * F(rnd.randint(-8, 8), 2) for _ in range(n)]
        r = ccs(xs, c, s)
        o = oracle_rules(xs, c, s)
        for k in o:
            assert r[k] == o[k]
            if o[k]:
                fired.add(k)
        assert r['in_control'] == (not any(o.values())) and r['z'] == [(x - c) / s for x in xs]
    assert fired == {'rule1', 'rule2', 'rule3', 'rule4'}


def test_rule_edges_exact():
    base = [0] * 8
    assert ccs([3], 0, 1)['rule1'] == [] and ccs([F(301, 100)], 0, 1)['rule1'] == [0]
    assert ccs([-3], 0, 1)['rule1'] == [] and ccs([F(-301, 100)], 0, 1)['rule1'] == [0]
    assert ccs([F(21, 10), 0, F(21, 10)], 0, 1)['rule2'] == [2]
    assert ccs([2, 0, 2], 0, 1)['rule2'] == [] and ccs([F(21, 10), 0, 0, F(21, 10)], 0, 1)['rule2'] == []
    assert ccs([F(21, 10), F(-21, 10), 0], 0, 1)['rule2'] == [] and ccs([F(21, 10), F(21, 10)], 0, 1)['rule2'] == [1]
    assert ccs([F(-21, 10), F(-21, 10)], 0, 1)['rule2'] == [1]
    assert ccs([F(11, 10)] * 4 + [0], 0, 1)['rule3'] == [3]
    assert ccs([F(11, 10)] * 3 + [0, F(11, 10)], 0, 1)['rule3'] == [4]
    assert ccs([1] * 5, 0, 1)['rule3'] == [] and ccs([F(11, 10)] * 3, 0, 1)['rule3'] == []
    assert ccs([F(-11, 10)] * 4, 0, 1)['rule3'] == [3]
    assert ccs([1] * 8, 0, 1)['rule4'] == [7] and ccs([1] * 7, 0, 1)['rule4'] == []
    assert ccs([-1] * 9, 0, 1)['rule4'] == [7, 8]
    assert ccs([1] * 7 + [0], 0, 1)['rule4'] == [] and ccs([1] * 3 + [0] + [1] * 4, 0, 1)['rule4'] == []
    assert ccs(base, 0, 1)['in_control'] is True and ccs([4], 0, 1)['in_control'] is False
    assert ccs([F(1, 2), F(3, 2)], 1, F(1, 2))['z'] == [-1, 1]


def test_capability_vs_oracle_random():
    rnd = random.Random(17)
    for _ in range(500):
        n = rnd.randint(2, 12)
        xs = [F(rnd.randint(0, 40), rnd.randint(1, 4)) for _ in range(n)]
        lo = F(rnd.randint(-20, 10))
        hi = lo + F(rnd.randint(1, 60), rnd.randint(1, 3))
        t = F(rnd.randint(1, 30), rnd.randint(1, 10))
        t = min(t, 10)
        r = cap(xs, lo, hi, t)
        m = sum(xs) / n
        v = (sum(x * x for x in xs) - n * m * m) / (n - 1)
        mg = min(hi - m, m - lo)
        assert r['mean'] == m and r['variance'] == v and r['cpk_margin'] == mg
        if v == 0:
            assert r['cp_squared'] is None and r['cpk_squared'] is None and r['cp_ok'] is True and r['cpk_ok'] == (mg > 0)
        else:
            assert r['cp_squared'] == (hi - lo) ** 2 / (36 * v) and r['cpk_squared'] == mg ** 2 / (9 * v)
            assert r['cp_ok'] == ((hi - lo) ** 2 >= 36 * t * t * v)
            assert r['cpk_ok'] == (mg >= 0 and mg ** 2 >= 9 * t * t * v)


def test_capability_hand_and_edges():
    r = cap([10, 11, 9, 10, 10, 11, 9], 4, 16, 1)
    assert r['variance'] == F(2, 3) and r['cp_squared'] == 6 and r['cpk_squared'] == 6 and r['cp_ok'] and r['cpk_ok']
    # Cp exactly equal to the target passes: sd = 1, limits 6 apart => Cp = 1
    xs = [9, 10, 11]
    assert cap(xs, 7, 13, 1)['cp_ok'] is True and cap(xs, 7, 13, F(101, 100))['cp_ok'] is False
    assert cap(xs, 7, 13, 1)['cpk_ok'] is True and cap(xs, 7, 13, F(101, 100))['cpk_ok'] is False
    # off-centre mean: Cp fine, Cpk poor, and a mean outside the limits gives a negative margin
    r = cap(xs, 7, 15, 1)
    assert r['cp_ok'] is True and r['cpk_margin'] == 3 and r['cpk_ok'] is True
    r = cap(xs, 8, 30, 1)
    assert r['cpk_margin'] == 2 and r['cpk_ok'] is False and r['cp_ok'] is True
    r = cap([20, 21, 22], 0, 10, 1)
    assert r['cpk_margin'] == -11 and r['cpk_ok'] is False
    assert cap([5, 5, 5], 0, 10, 1)['cp_ok'] is True and cap([5, 5, 5], 0, 10, 1)['cpk_ok'] is True
    assert cap([5, 5, 5], 5, 10, 1)['cpk_ok'] is False and cap([5, 5, 5], 0, 5, 1)['cpk_ok'] is False


def test_caps_accept():
    ccs([-1000000] * 100, 1000000, 1000000)
    ccs([1000000], -1000000, 1)
    ccs([0], 0, F(1, 2 ** 32 - 1))
    ccs([F(2 ** 31 + 1, 2 ** 31 + 3)], 0, 1)
    cap([-1000000, 1000000], -1000000, 1000000, 10)
    cap([1, 2], 0, 1, F(1, 2 ** 32 - 1))


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


T, V = TypeError, ValueError


def test_pins_chart():
    err(ccs, T, 'points must be a list or tuple', 'ab', 0, 1)
    err(ccs, V, 'points count must be between 1 and 100', [], 0, 1)
    err(ccs, V, 'points count must be between 1 and 100', [0] * 101, 0, 1)
    for bad in (True, 1.0, '1', None):
        err(ccs, T, 'point value must be a nonbool int or Fraction', [0, bad], 0, 1)
        err(ccs, T, 'center must be a nonbool int or Fraction', [0], bad, 1)
        err(ccs, T, 'sigma must be a nonbool int or Fraction', [0], 0, bad)
    err(ccs, V, 'rational values must fit 32 bits', [F(1, 2 ** 32)], 0, 1)
    err(ccs, V, 'rational values must fit 32 bits', [F(2 ** 32 + 1, 2 ** 32 + 3)], 0, 1)
    err(ccs, V, 'point value must be between -1000000 and 1000000', [1000001], 0, 1)
    err(ccs, V, 'point value must be between -1000000 and 1000000', [-1000001], 0, 1)
    err(ccs, V, 'center must be between -1000000 and 1000000', [0], 1000001, 1)
    err(ccs, V, 'center must be between -1000000 and 1000000', [0], -1000001, 1)
    err(ccs, V, 'sigma must be greater than 0 and at most 1000000', [0], 0, 0)
    err(ccs, V, 'sigma must be greater than 0 and at most 1000000', [0], 0, -1)
    err(ccs, V, 'sigma must be greater than 0 and at most 1000000', [0], 0, 1000001)
    err(ccs, V, 'rational values must fit 32 bits', [0], F(1, 2 ** 32), 1)
    err(ccs, V, 'rational values must fit 32 bits', [0], 0, F(1, 2 ** 32))


def test_pins_capability():
    err(cap, T, 'samples must be a list or tuple', 'ab', 0, 1, 1)
    err(cap, V, 'samples count must be between 1 and 100', [], 0, 1, 1)
    err(cap, V, 'samples count must be between 1 and 100', [0] * 101, 0, 1, 1)
    err(cap, V, 'at least 2 samples are needed', [1], 0, 2, 1)
    for bad in (True, 1.0, None):
        err(cap, T, 'sample value must be a nonbool int or Fraction', [1, bad], 0, 2, 1)
        err(cap, T, 'lsl must be a nonbool int or Fraction', [1, 2], bad, 2, 1)
        err(cap, T, 'usl must be a nonbool int or Fraction', [1, 2], 0, bad, 1)
        err(cap, T, 'target must be a nonbool int or Fraction', [1, 2], 0, 2, bad)
    err(cap, V, 'sample value must be between -1000000 and 1000000', [1, 1000001], 0, 2, 1)
    err(cap, V, 'sample value must be between -1000000 and 1000000', [1, -1000001], 0, 2, 1)
    err(cap, V, 'specification limits must be between -1000000 and 1000000', [1, 2], -1000001, 2, 1)
    err(cap, V, 'specification limits must be between -1000000 and 1000000', [1, 2], 0, 1000001, 1)
    err(cap, V, 'specification limits must be between -1000000 and 1000000', [1, 2], 1000001, 1000001, 1)
    err(cap, V, 'specification limits must be between -1000000 and 1000000', [1, 2], -1000001, -1000001, 1)
    err(cap, V, 'lsl must be below usl', [1, 2], 2, 2, 1)
    err(cap, V, 'lsl must be below usl', [1, 2], 3, 2, 1)
    err(cap, V, 'target must be greater than 0 and at most 10', [1, 2], 0, 2, 0)
    err(cap, V, 'target must be greater than 0 and at most 10', [1, 2], 0, 2, 11)
    err(cap, V, 'target must be greater than 0 and at most 10', [1, 2], 0, 2, F(101, 10))
    err(cap, V, 'rational values must fit 32 bits', [1, 2], 0, 2, F(1, 2 ** 32))
    err(cap, V, 'rational values must fit 32 bits', [1, 2], F(1, 2 ** 32), 2, 1)


def test_every_position_validated():
    for pos in range(3):
        v = [0, 0, 0]
        v[pos] = 1.5
        err(ccs, T, 'point value must be a nonbool int or Fraction', v, 0, 1)
        err(cap, T, 'sample value must be a nonbool int or Fraction', v, 0, 2, 1)


def test_rule4_fires_at_exactly_eight_points_from_the_start():
    assert ccs([1] * 8, 0, 1)['rule4'] == [7]
    assert ccs([1] * 7, 0, 1)['rule4'] == []
    assert ccs([-1] * 8, 0, 1)['rule4'] == [7]


def test_spec_limit_edges_exact():
    L = 10 ** 6
    cap([1, 2], -L, L, 1)
    cap([1, 2], -L, -L + 1, 1)
    cap([1, 2], L - 1, L, 1)
    m = 'specification limits must be between -1000000 and 1000000'
    err(cap, ValueError, m, [1, 2], -L - 1, 0, 1)
    err(cap, ValueError, m, [1, 2], 0, L + 1, 1)
    err(cap, ValueError, m, [1, 2], -L - 1, -L, 1)
    err(cap, ValueError, m, [1, 2], L, L + 1, 1)


def test_capability_equality_and_margin_edges():
    r = cap([0, 1, 2], -2, 4, 1)           # cp2 == 1 and cpk2 == 1 exactly, target 1
    assert r['cp_squared'] == 1 and r['cpk_squared'] == 1 and r['cp_ok'] is True and r['cpk_ok'] is True
    r = cap([-F(1, 100), F(1, 100)], -F(1, 2), 10, 1)   # margin 1/2, below 1 but positive
    assert r['cpk_margin'] == F(1, 2) and r['cpk_ok'] is True
    r = cap([1, F(11, 10)], 0, 1, F(1, 100))           # mean outside the limits: margin negative
    assert r['cpk_margin'] == -F(1, 20) and r['cpk_squared'] > F(1, 10000) and r['cpk_ok'] is False
    assert cap([F(1, 2)] * 2, 0, 1, 1)['cpk_ok'] is True        # zero variance, margin 1/2
    assert cap([0, 0], 0, 1, 1)['cpk_ok'] is False              # zero variance, margin 0
    assert cap([F(3, 2)] * 2, 0, 1, 1)['cpk_ok'] is False       # zero variance, margin -1/2
    assert cap([F(1, 2)] * 2, 0, 1, 1)['cp_ok'] is True


def test_numerator_alone_33_bits_refused_first():
    m = 'rational values must fit 32 bits'
    err(ccs, ValueError, m, [2 ** 32], 0, 1)
    err(ccs, ValueError, m, [0], 2 ** 32, 1)
    err(ccs, ValueError, m, [0], 0, 2 ** 32)
    err(cap, ValueError, m, [2 ** 32, 1], 0, 2, 1)
    err(cap, ValueError, m, [1, 2], 2 ** 32, 2, 1)
    err(cap, ValueError, m, [1, 2], 0, 2 ** 32, 1)
    err(cap, ValueError, m, [1, 2], 0, 2, 2 ** 32)


def test_rule4_needs_all_eight_on_one_side_and_runs_continue():
    assert ccs([-1] * 7 + [1], 0, 1)['rule4'] == []
    assert ccs([1] * 7 + [-1], 0, 1)['rule4'] == []
    assert ccs([1] * 9, 0, 1)['rule4'] == [7, 8]
    assert ccs([1] * 4 + [-1] + [1] * 8, 0, 1)['rule4'] == [12]
    assert ccs([0] + [1] * 7, 0, 1)['rule4'] == []


def test_equal_limits_at_the_edge_get_the_order_message():
    L = 10 ** 6
    err(cap, ValueError, 'lsl must be below usl', [1, 2], L, L, 1)
    err(cap, ValueError, 'lsl must be below usl', [1, 2], -L, -L, 1)


def test_rule3_needs_four_of_the_last_five_points_exact():
    # z = [0, 2, 0, 2, 2, 2]: at index 5 the last 5 points hold 4 above 1 sigma, so rule 3 fires at 5 only
    r = ccs([0, 2, 0, 2, 2, 2], 0, 1)
    assert r['rule3'] == [5]
    assert r['rule1'] == [] and r['rule2'] == [] and r['rule4'] == [] and r['in_control'] is False
    r = ccs([0, -2, 0, -2, -2, -2], 0, 1)
    assert r['rule3'] == [5]
    # only 3 of 5 beyond: no fire
    assert ccs([0, 2, 0, 2, 2], 0, 1)['rule3'] == []
    assert ccs([2, 2, 0, 2, 2], 0, 1)['rule3'] == [4]


def test_rule4_window_is_exactly_eight_points():
    assert ccs([1] * 8 + [-1], 0, 1)['rule4'] == [7]
    assert ccs([-1] * 8 + [1], 0, 1)['rule4'] == [7]
    assert ccs([1] * 8 + [-1] + [1] * 8, 0, 1)['rule4'] == [7, 16]
