import random
from decimal import Decimal
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.pcm_mix import mix_pcm as mix

T, V = TypeError, ValueError


def oracle(tracks, gains):
    n = len(tracks[0])
    exact, out, clip = [], [], 0
    for i in range(n):
        v = F(0)
        for t, g in zip(tracks, gains):
            v += F(g) * t[i]
        exact.append(v)
        # round half up with integer arithmetic on the exact fraction
        r = (2 * v.numerator + v.denominator) // (2 * v.denominator)
        c = r
        if c > 32767:
            c = 32767
        if c < -32768:
            c = -32768
        clip += r != c
        out.append(c)
    return {'samples': out, 'exact': exact, 'clipped': clip, 'peak': max(abs(v) for v in exact)}


def err(exc, msg, *a):
    with pytest.raises(exc) as e:
        mix(*a)
    assert str(e.value) == msg


def test_hand_cases():
    r = mix([[100, -100, 7]], [1])
    assert r == {'samples': [100, -100, 7], 'exact': [F(100), F(-100), F(7)], 'clipped': 0, 'peak': F(100)}
    assert mix([[1], [3]], [F(1, 2), F(1, 2)])['samples'] == [2]
    # rounding half up: 1/2 -> 1, -1/2 -> 0, 3/2 -> 2, -3/2 -> -1
    r = mix([[1, -1, 3, -3]], [F(1, 2)])
    assert r['samples'] == [1, 0, 2, -1] and r['exact'] == [F(1, 2), F(-1, 2), F(3, 2), F(-3, 2)]
    assert r['peak'] == F(3, 2) and r['clipped'] == 0
    # clamping: 32767 * 2 clips; -32768 * 2 clips; exactly at the limits does not clip
    r = mix([[32767, -32768, 16384, -16384, 20000]], [2])
    assert r['samples'] == [32767, -32768, 32767, -32768, 32767] and r['clipped'] == 4
    assert r['peak'] == 65536
    r = mix([[32767, -32768]], [1])
    assert r['samples'] == [32767, -32768] and r['clipped'] == 0
    # 32767.4 rounds to 32767 without counting as a clip; 32767.5 rounds to 32768 and does
    r = mix([[32767], [2]], [1, F(1, 5)])      # 32767.4 rounds to 32767, no clip
    assert r['samples'] == [32767] and r['clipped'] == 0 and r['exact'] == [F(163837, 5)]
    r = mix([[32767], [1]], [1, F(1, 2)])      # 32767.5 -> 32768 -> clipped to 32767
    assert r['samples'] == [32767] and r['clipped'] == 1 and r['exact'] == [F(65535, 2)]
    r = mix([[-32768], [-1]], [1, F(1, 2)])    # -32768.5 -> -32768 by half up, which is in range, no clip
    assert r['samples'] == [-32768] and r['clipped'] == 0
    r = mix([[-32768], [-3]], [1, F(1, 2)])    # -32769.5 -> -32769 -> clipped
    assert r['samples'] == [-32768] and r['clipped'] == 1
    assert mix([[5]], [0])['samples'] == [0] and mix([[5]], [0])['peak'] == 0
    assert type(mix([[5]], [1])['exact'][0]) is F and type(mix([[5]], [1])['peak']) is F


def test_random_vs_oracle():
    rnd = random.Random(579)
    clipped = frac = 0
    for _ in range(500):
        k, n = rnd.randint(1, 4), rnd.randint(1, 8)
        big = rnd.random() < 0.5
        tracks = [[rnd.choice([-32768, 32767, rnd.randint(-32768, 32767)]) if big else rnd.randint(-50, 50)
                   for _ in range(n)] for _ in range(k)]
        gains = [rnd.choice([0, 1, 4, F(rnd.randint(0, 16), rnd.choice([1, 2, 3, 4, 7]))]) for _ in range(k)]
        gains = [g if g <= 4 else F(4) for g in gains]
        r = mix(tracks, gains)
        w = oracle(tracks, gains)
        assert r == w
        clipped += r['clipped'] > 0
        frac += any(v.denominator != 1 for v in r['exact'])
    assert clipped > 50 and frac > 50
    t = [[1, 2, 3], [4, 5, 6]]
    mix(tuple(tuple(x) for x in t), (1, 2))
    assert mix(t, [1, 2]) == mix(tuple(map(tuple, t)), (1, 2)) and t == [[1, 2, 3], [4, 5, 6]]


def test_limits_accepted():
    mix([[0] * 64] * 4, [4] * 4)
    mix([[-32768, 32767]], [F(2 ** 32 - 1, 2 ** 31)])
    mix([[1]], [F(1, 2 ** 32 - 1)])
    assert mix([[1] * 64] * 4, [0, 0, 0, 0])['samples'] == [0] * 64
    mix([[0]], [4])


def test_pins_types_and_ranges():
    for bad in ('ab', {1}, None, 5, (x for x in [[1]])):
        err(T, 'tracks must be a list or tuple', bad, [1])
    err(V, 'track count must be between 1 and 4', [], [])
    err(V, 'track count must be between 1 and 4', [[1]] * 5, [1] * 5)
    for bad in ('ab', None, 5, {1: 1}):
        err(T, 'track must be a list or tuple', [bad], [1])
    err(V, 'track length must be between 1 and 64', [[]], [1])
    err(V, 'track length must be between 1 and 64', [[1] * 65], [1])
    err(V, 'all tracks must have the same length', [[1, 2], [1]], [1, 1])
    err(V, 'all tracks must have the same length', [[1], [1, 2]], [1, 1])
    for bad in (True, 1.0, F(1), '1', None, Decimal(1)):
        err(T, 'sample must be a nonbool int', [[1, bad]], [1])
    err(V, 'sample must be between -32768 and 32767', [[32768]], [1])
    err(V, 'sample must be between -32768 and 32767', [[-32769]], [1])
    for bad in ('ab', None, 5):
        err(T, 'gains must be a list or tuple', [[1]], bad)
    err(V, 'gains must have one entry per track', [[1]], [])
    err(V, 'gains must have one entry per track', [[1]], [1, 1])
    err(V, 'gains must have one entry per track', [[1], [1]], [1])
    for bad in (True, 1.0, '1', None, Decimal(1)):
        err(T, 'gain must be a nonbool int or Fraction', [[1]], [bad])
    for bad in (F(2 ** 32 + 1, 2 ** 30 + 1), F(1, 2 ** 32), F(1, 2 ** 32 + 1)):
        assert bad.numerator.bit_length() > 32 or bad.denominator.bit_length() > 32
        err(V, 'rational values must fit 32 bits', [[1]], [bad])
    for bad in (-1, F(-1, 2), 5, F(17, 4)):
        err(V, 'gain must be between 0 and 4', [[1]], [bad])


def test_check_order():
    err(T, 'tracks must be a list or tuple', 'x', 'y')
    err(V, 'track count must be between 1 and 4', [], 'y')
    err(V, 'track count must be between 1 and 4', [[1]] * 5, 'y')
    err(T, 'track must be a list or tuple', ['x', [1, 2], 5], 'y')
    err(V, 'track length must be between 1 and 64', [[], 'x'], 'y')
    err(V, 'track length must be between 1 and 64', [[1], [1] * 65], 'y')
    err(V, 'all tracks must have the same length', [[1], [1, 'x']], 'y')
    err(V, 'all tracks must have the same length', [[1, 2], [1, 2, 3], 'x'], 'y')
    err(T, 'sample must be a nonbool int', [[True, 99999]], 'y')
    err(V, 'sample must be between -32768 and 32767', [[99999, True]], 'y')
    err(V, 'sample must be between -32768 and 32767', [[1, 99999, True]], 'y')
    err(V, 'sample must be between -32768 and 32767', [[1, 99999], [1.5, 2]], 'y')
    err(T, 'sample must be a nonbool int', [[1, 2], [1, 2.5], [1]], 'y')


class IntSub(int):
    pass


class FracSub(F):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def test_subclass_witnesses_and_every_position():
    err(T, 'tracks must be a list or tuple', ListSub([[1]]), [1])
    err(T, 'tracks must be a list or tuple', TupleSub([[1]]), [1])
    err(T, 'track must be a list or tuple', [ListSub([1])], [1])
    err(T, 'track must be a list or tuple', [[1], TupleSub([1])], [1, 1])
    err(T, 'gains must be a list or tuple', [[1]], ListSub([1]))
    err(T, 'gains must be a list or tuple', [[1]], TupleSub([1]))
    err(T, 'sample must be a nonbool int', [[IntSub(1)]], [1])
    err(T, 'sample must be a nonbool int', [[1, 2], [3, IntSub(4)]], [1, 1])
    err(T, 'gain must be a nonbool int or Fraction', [[1]], [IntSub(1)])
    err(T, 'gain must be a nonbool int or Fraction', [[1]], [FracSub(1)])
    err(T, 'gain must be a nonbool int or Fraction', [[1], [1]], [1, FracSub(1, 2)])
    # a bad value at every sample position of every track is found
    for k in range(3):
        for i in range(4):
            tr = [[0] * 4 for _ in range(3)]
            tr[k][i] = 40000
            err(V, 'sample must be between -32768 and 32767', tr, [1, 1, 1])
    for k in range(3):
        g = [1, 1, 1]
        g[k] = 5
        err(V, 'gain must be between 0 and 4', [[1]] * 3, g)
    # the last position of the last track clips exactly when it should
    tr = [[0, 0, 0], [0, 0, 32767]]
    assert mix(tr, [1, 1])['samples'] == [0, 0, 32767] and mix(tr, [1, 2])['clipped'] == 1
