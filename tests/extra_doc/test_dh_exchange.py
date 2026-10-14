import copy
import random

import pytest

from sugarcode.extra_doc import dh_exchange as m
from sugarcode.extra_doc.dh_exchange import ProtocolError, dh_exchange as run

KEYS = "data keys must be exactly a, b, g, p"
PRIMES = [5, 7, 11, 13, 23, 101, 997, 1009, 9973, 10007]


def d(p=23, g=5, a=6, b=15):
    return {"p": p, "g": g, "a": a, "b": b}


def bad(data, msg):
    with pytest.raises(ProtocolError) as e:
        run(data)
    assert str(e.value) == msg


def slow_pow(base, e, p):
    r = 1
    for _ in range(e):
        r = r * base % p
    return r


def check(x):
    o = run(x)
    p, g, a, b = x["p"], x["g"], x["a"], x["b"]
    A, B = slow_pow(g, a, p), slow_pow(g, b, p)
    assert (o["public_a"], o["public_b"]) == (A, B)
    assert o["shared_a"] == slow_pow(B, a, p) and o["shared_b"] == slow_pow(A, b, p)
    assert o["agree"] is True and o["shared_a"] == slow_pow(g, a * b, p)
    xs = [e for e in range(1, p) if slow_pow(g, e, p) == A] if p < 2000 else None
    if xs is not None:
        assert o["recovered_exponent"] == (xs[0] if xs else None)
        if xs:
            assert o["recovered_shared"] == slow_pow(B, xs[0], p) and o["attack_matches"] is True
        else:
            assert o["recovered_shared"] is None and o["attack_matches"] is False
    return o


def test_textbook_case():
    # p=23 g=5 a=6 b=15: A=8, B=19, shared 2 ; 5 is a primitive root so 6 is the smallest exponent for 8
    o = run(d())
    assert (o["public_a"], o["public_b"], o["shared_a"], o["shared_b"]) == (8, 19, 2, 2)
    assert o["agree"] is True and o["recovered_exponent"] == 6 and o["recovered_shared"] == 2
    assert o["attack_matches"] is True and o["status"] == "completed"
    assert o["claims"] == {"secure": False, "safe_parameters": False, "active_attacker": False, "real_world": False}
    assert len(o["not_claimed"]) == 4


def test_smallest_exponent_when_order_is_short():
    # p=13, g=3: 3^3 = 27 = 1 mod 13, order 3. a=4 -> A = 3^4 = 81 = 3 mod 13; smallest x = 1
    o = run(d(13, 3, 4, 7))
    assert o["public_a"] == 3 and o["recovered_exponent"] == 1
    assert o["attack_matches"] is True and o["agree"] is True
    # p=7, g=2: order 3 (2,4,1). a=5 -> A = 32 mod 7 = 4 ; smallest x = 2
    o = run(d(7, 2, 5, 3))
    assert o["public_a"] == 4 and o["recovered_exponent"] == 2 and o["public_b"] == 1
    assert o["shared_a"] == 1 and o["shared_b"] == 1 and o["recovered_shared"] == 1


def test_small_exhaustive():
    for p in (5, 7, 11, 13):
        for g in range(2, p - 1):
            for a in range(1, p - 1):
                for b in range(1, p - 1):
                    check(d(p, g, a, b))


def test_random():
    rng = random.Random(584)
    for _ in range(300):
        p = rng.choice(PRIMES[:7])
        check(d(p, rng.randint(2, p - 2), rng.randint(1, p - 2), rng.randint(1, p - 2)))
    for _ in range(100):
        p = rng.choice([1009, 9973, 10007])
        x = d(p, rng.randint(2, p - 2), rng.randint(1, p - 2), rng.randint(1, p - 2))
        o = run(x)
        assert o["agree"] is True and o["shared_a"] == pow(x["g"], x["a"] * x["b"], p)
        assert o["attack_matches"] is True


def test_edges():
    check(d(5, 2, 1, 1))
    check(d(5, 3, 3, 3))
    o = run(d(10007, 10005, 10005, 10005))
    assert o["agree"] is True and o["public_a"] == pow(10005, 10005, 10007)


@pytest.mark.parametrize("p", [6, 9, 15, 21, 25, 100, 10005, 9999, 1001, 10000])
def test_composite(p):
    bad(d(p=p), "p must be prime")


def test_p_range():
    for p in (-5, 0, 1, 2, 3, 4):
        bad(d(p=p), "p must be 5 to 10007")
    for p in (10008, 10009, 10**30):
        bad(d(p=p), "p must be 5 to 10007")
    run(d(p=5, g=2, a=1, b=1))
    run(d(p=10007, g=2, a=1, b=1))


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint(s):
    for k in ("p", "g", "a", "b"):
        x = d()
        x[k] = s
        bad(x, k + " must be an int")


def test_slot_ranges():
    for k, lo in (("g", 2), ("a", 1), ("b", 1)):
        for v in (lo - 1, 22, 23, 10**30, -(10**30)):
            x = d()
            x[k] = v
            bad(x, "%s must be %d to p-2" % (k, lo))
        x = d()
        x[k] = lo
        run(x)
        x[k] = 21
        run(x)


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("p", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in list(d()):
        x = d()
        del x[k]
        bad(x, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["real_world"] = True
    c = run(x)
    assert c["claims"]["real_world"] is False
    assert len(m.NOT_CLAIMED) == 4 and all(v is False for v in m.CLAIMS.values())


class _SubInt(int):
    pass


class _Quirky(int):
    """int subclass with lying arithmetic and comparisons."""
    def __sub__(self, o):
        return 0

    def __add__(self, o):
        return 1

    def __mul__(self, o):
        return 0

    def __gt__(self, o):
        return False

    def __lt__(self, o):
        return False


def _int_paths(x, path=()):
    if type(x) is int:
        yield path
    elif isinstance(x, dict):
        for k in x:
            yield from _int_paths(x[k], path + (k,))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _int_paths(v, path + (i,))


def _put(x, path, val):
    y = copy.deepcopy(x)
    t = y
    for k in path[:-1]:
        t = t[k]
    t[path[-1]] = val
    return y


def test_int_subclasses_refused_in_every_int_slot():
    base = {"p": 23, "g": 5, "a": 6, "b": 15}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(ProtocolError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x


class _SubStr(str):
    pass


class _LyingStr(str):
    """str subclass that hashes like 1 and equals 1."""
    def __hash__(self):
        return 1

    def __eq__(self, o):
        return o == 1 or str.__eq__(self, o)


def _variants(x):
    """Yield every copy of x with one str leaf or one dict key replaced by bytes or a str subclass."""
    import copy as _c
    def walk(node, path):
        if type(node) is str:
            yield path, "leaf"
        elif isinstance(node, dict):
            for k in node:
                if type(k) is str:
                    yield path + (k,), "key"
                yield from walk(node[k], path + (k,))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, path + (i,))
    for path, kind in walk(x, ()):
        for mk in (lambda s: s.encode(), _SubStr, _LyingStr):
            if kind == "key" and mk is _SubStr:
                continue   # a plain str subclass hashes and compares like its key: indistinguishable as a dict key
            y = _c.deepcopy(x)
            t = y
            for k in path[:-1]:
                t = t[k]
            last = path[-1]
            if kind == "leaf":
                t[last] = mk(t[last])
            else:
                t2 = {}
                for k, v in t.items():
                    t2[mk(k) if k == last else k] = v
                if len(path) == 1:
                    y = t2
                else:
                    u = y
                    for k in path[:-2]:
                        u = u[k]
                    u[path[-2]] = t2
            yield y


def test_nonexact_str_refused_in_every_str_slot_and_key():
    base = {"p": 23, "g": 5, "a": 6, "b": 15}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(ProtocolError):
            run(y)
    assert n >= 2
