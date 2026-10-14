import copy
import random

import pytest

from sugarcode.extra_doc import layered_defense as m
from sugarcode.extra_doc.layered_defense import DefenseError, layered_defense as run

KEYS = "data keys must be exactly attacks, layers"
NLAY = "layers must be a list of 1 to 8 layers"
NATK = "attacks must be a list of 1 to 10 attacks"


def d(layers=(10, 20, 30), attacks=(5, 10, 11, 30, 60, 61, 100)):
    return {"layers": list(layers), "attacks": list(attacks)}


def bad(data, msg):
    with pytest.raises(DefenseError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(layers, attacks):
    """Independent: prefix sums. An attack p is stopped at the first layer k with p <= prefix[k+1]."""
    prefix = [0]
    for s in layers:
        prefix.append(prefix[-1] + s)
    rows, counts = [], [0] * len(layers)
    for p in attacks:
        k = next((k for k in range(len(layers)) if p <= prefix[k + 1]), None)
        if k is None:
            rows.append({"power": p, "blocked_at": None, "residual": p - prefix[-1]})
        else:
            rows.append({"power": p, "blocked_at": k, "residual": p - prefix[k]})
            counts[k] += 1
    return rows, counts


def check(x):
    o = run(x)
    rows, counts = oracle(x["layers"], x["attacks"])
    assert o["attacks"] == rows and o["blocked_counts"] == counts
    br = sum(1 for r in rows if r["blocked_at"] is None)
    assert o["breached"] == br and o["blocked"] == len(rows) - br
    return o


def test_hand_worked():
    # layers 10,20,30 : prefix 10,30,60. 5 -> layer0 (5<=10); 10 -> layer0 (10<=10);
    # 11 -> passes 0 (left 1), blocked at 1 (1<=20); 30 -> layer1 (left 20 <= 20);
    # 60 -> layer2 (left 30 <= 30); 61 -> breached, left 1; 100 -> breached, left 40
    o = run(d())
    A = o["attacks"]
    assert [(a["power"], a["blocked_at"], a["residual"]) for a in A] == [
        (5, 0, 5), (10, 0, 10), (11, 1, 1), (30, 1, 20), (60, 2, 30), (61, None, 1), (100, None, 40)]
    assert o["blocked_counts"] == [2, 2, 1] and o["breached"] == 2 and o["blocked"] == 5
    assert o["status"] == "completed"
    assert o["claims"] == {"designs_defenses": False, "measures_security": False, "real_attacks": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_zero_strength_and_zero_power():
    o = run(d(layers=[0, 0], attacks=[0, 1]))
    assert [(a["blocked_at"], a["residual"]) for a in o["attacks"]] == [(0, 0), (None, 1)]
    o = run(d(layers=[0, 5], attacks=[3]))
    assert o["attacks"][0]["blocked_at"] == 1 and o["attacks"][0]["residual"] == 3
    o = run(d(layers=[5, 0], attacks=[5, 6]))
    assert [(a["blocked_at"], a["residual"]) for a in o["attacks"]] == [(0, 5), (None, 1)]


def test_single_layer_boundary():
    o = run(d(layers=[7], attacks=[6, 7, 8]))
    assert [(a["blocked_at"], a["residual"]) for a in o["attacks"]] == [(0, 6), (0, 7), (None, 1)]
    assert o["blocked_counts"] == [2] and o["breached"] == 1 and o["blocked"] == 2


def test_attacks_independent_and_order_kept():
    o1 = run(d(layers=[10, 10], attacks=[15, 25, 15]))
    assert [a["blocked_at"] for a in o1["attacks"]] == [1, None, 1]
    assert [a["power"] for a in o1["attacks"]] == [15, 25, 15]
    assert o1["blocked_counts"] == [0, 2]


def test_random():
    rng = random.Random(524)
    for _ in range(1500):
        layers = [rng.randint(0, 100) for _ in range(rng.randint(1, 8))]
        tot = sum(layers)
        attacks = [rng.choice([rng.randint(0, 1000), max(0, tot + rng.randint(-1, 1)), rng.randint(0, tot)])
                   for _ in range(rng.randint(1, 10))]
        check(d(layers, attacks))


def test_caps():
    run(d(layers=[1] * 8, attacks=[1] * 10))
    bad(d(layers=[1] * 9), NLAY)
    bad(d(layers=[1] * 10**5), NLAY)
    bad(d(layers=[]), NLAY)
    bad(d(attacks=[1] * 11), NATK)
    bad(d(attacks=[1] * 10**5), NATK)
    bad(d(attacks=[]), NATK)


@pytest.mark.parametrize("v", [True, 1, "ab", None, (1, 2), {}])
def test_noncontainers(v):
    x = d()
    x["layers"] = v
    bad(x, NLAY)
    x = d()
    x["attacks"] = v
    bad(x, NATK)


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint(s):
    x = d()
    x["layers"][1] = s
    bad(x, "layers entry must be an int")
    x = d()
    x["attacks"][1] = s
    bad(x, "attacks entry must be an int")


@pytest.mark.parametrize("s", [-1, 101, 10**30, -(10**30)])
def test_layer_range(s):
    x = d()
    x["layers"][0] = s
    bad(x, "layers entry must be 0 to 100")


@pytest.mark.parametrize("s", [-1, 1001, 10**30, -(10**30)])
def test_attack_range(s):
    x = d()
    x["attacks"][0] = s
    bad(x, "attacks entry must be 0 to 1000")


def test_edges():
    check(d(layers=[100] * 8, attacks=[0, 800, 801, 1000]))
    check(d(layers=[0], attacks=[0, 1000]))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("layers", 1)]])
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


def test_tuple_refused():
    x = d()
    x["layers"] = (1, 2)
    bad(x, NLAY)
    x = d()
    x["attacks"] = (1, 2)
    bad(x, NATK)


def test_no_mutation_determinism_fresh_claims():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["real_world"] = True
    a["attacks"][0]["residual"] = 99
    a["blocked_counts"][0] = 99
    c = run(x)
    assert c["claims"]["real_world"] is False and c["attacks"][0]["residual"] == 5 and c["blocked_counts"][0] == 2
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
    base = {"layers": [10, 20, 30], "attacks": [5, 10, 11, 30, 60, 61, 100]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(DefenseError) as e:
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
    base = {"layers": [10, 20, 30], "attacks": [5, 10, 11, 30, 60, 61, 100]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(DefenseError):
            run(y)
    assert n >= 2
