import random
import pytest
from sugarcode.extra_doc.fuzz_inputs import fuzz_inputs as fz

T, V = TypeError, ValueError
M = 2 ** 32


class IntSub(int):
    pass


def jump(seed, k):
    # closed form of k steps: state_k = a^k * seed + c * (a^k - 1) / (a - 1), mod 2^32 (exact big integers)
    a, c = 1664525, 1013904223
    return (a ** k * seed + c * ((a ** k - 1) // (a - 1))) % M


def oracle(seed, n, lo, hi):
    vals = [lo + (jump(seed, i) >> 8) % (hi - lo + 1) for i in range(1, n + 1)]
    return {'values': vals, 'final_state': jump(seed, n)}


def test_hand_cases():
    # seed 0: first state is c = 1013904223; (c >> 8) = 3960563
    assert 1013904223 >> 8 == 3960563
    assert fz(0, 1, 0, 9) == {'values': [3960563 % 10], 'final_state': 1013904223}
    assert fz(0, 1, 5, 5) == {'values': [5], 'final_state': 1013904223}
    assert fz(0, 1, -3, 3)['values'] == [-3 + 3960563 % 7]
    # second step by hand: 1664525 * 1013904223 + 1013904223 mod 2^32
    s2 = (1664525 * 1013904223 + 1013904223) % M
    assert s2 == 1196435762
    assert fz(0, 2, 0, 99) == {'values': [3960563 % 100, (s2 >> 8) % 100], 'final_state': s2}
    assert fz(4294967295, 1, 0, 0) == {'values': [0], 'final_state': (1664525 * 4294967295 + 1013904223) % M}


def test_random_vs_closed_form_oracle():
    rnd = random.Random(602)
    for _ in range(300):
        seed = rnd.choice([0, 1, M - 1, rnd.randrange(M)])
        n = rnd.choice([1, 2, 3, rnd.randint(1, 60)])
        lo = rnd.choice([0, -1000000, rnd.randint(-100, 100)])
        hi = lo + rnd.choice([0, 1, 2, 9, rnd.randint(0, 5000)])
        hi = min(hi, 1000000)
        r = fz(seed, n, lo, hi)
        assert r == oracle(seed, n, lo, hi)
        assert all(lo <= v <= hi for v in r['values']) and len(r['values']) == n
        assert fz(seed, n, lo, hi) == r                               # repeatable
    r = fz(7, 1000, -1000000, 1000000)
    assert r == oracle(7, 1000, -1000000, 1000000)


def test_prefix_and_continuation_laws():
    long = fz(123, 50, -5, 5)
    for k in (1, 7, 49):
        short = fz(123, k, -5, 5)
        assert long['values'][:k] == short['values']
        rest = fz(short['final_state'], 50 - k, -5, 5)             # continuing from the saved state
        assert short['values'] + rest['values'] == long['values'] and rest['final_state'] == long['final_state']
    assert fz(1, 30, 0, 3)['values'] != fz(2, 30, 0, 3)['values']


def test_edges_accepted():
    fz(0, 1, 0, 0)
    fz(M - 1, 1000, -1000000, 1000000)
    fz(0, 1, 1000000, 1000000)
    fz(0, 1, -1000000, -1000000)
    assert len(fz(5, 1000, 0, 1)['values']) == 1000


def err(exc, msg, *a):
    with pytest.raises(exc) as e:
        fz(*a)
    assert str(e.value) == msg


def test_pins_every_slot():
    ok = [3, 4, 0, 9]
    names = ['seed', 'count', 'low', 'high']
    for pos, name in enumerate(names):
        for bad in (True, False, 1.0, '1', None, IntSub(1), [1]):
            a = list(ok)
            a[pos] = bad
            err(T, name + ' must be a nonbool int', *a)
    err(V, 'seed must be between 0 and 4294967295', -1, 4, 0, 9)
    err(V, 'seed must be between 0 and 4294967295', M, 4, 0, 9)
    err(V, 'count must be between 1 and 1000', 3, 0, 0, 9)
    err(V, 'count must be between 1 and 1000', 3, 1001, 0, 9)
    err(V, 'low must be between -1000000 and 1000000', 3, 4, -1000001, 9)
    err(V, 'low must be between -1000000 and 1000000', 3, 4, 1000001, 1000001)
    err(V, 'high must be between -1000000 and 1000000', 3, 4, 0, 1000001)
    err(V, 'high must be between -1000000 and 1000000', 3, 4, -1000000, -1000001)
    err(V, 'low must not exceed high', 3, 4, 1, 0)
    err(V, 'low must not exceed high', 3, 4, 1000000, -1000000)


def test_order_of_checks():
    err(T, 'seed must be a nonbool int', True, 0, 5, 1)
    err(V, 'seed must be between 0 and 4294967295', -1, 'x', 'y', 'z')
    err(T, 'count must be a nonbool int', 1, 'x', 5, 1)
    err(V, 'count must be between 1 and 1000', 1, 0, 'y', 'z')
    err(T, 'low must be a nonbool int', 1, 1, 'y', 'z')
    err(V, 'low must be between -1000000 and 1000000', 1, 1, 2000000, 'z')
    err(T, 'high must be a nonbool int', 1, 1, 5, 'z')
    err(V, 'high must be between -1000000 and 1000000', 1, 1, 5, 2000000)
    err(V, 'low must not exceed high', 1, 1, 5, 4)
