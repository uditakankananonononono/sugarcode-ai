import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import consequence_effect as m
from sugarcode.extra_doc.consequence_effect import OperantError, consequence_effect as run

KEYS = "data keys must be exactly intervals"
NI = "intervals must be a list of 2 to 12 intervals"
EI = "each interval must be a list of [count, consequence]"
CK = "consequence must be one of reward, punish, none"


def d(iv=((2, "reward"), (6, "reward"), (7, "punish"), (3, "none"), (3, "reward"))):
    return {"intervals": [list(e) for e in iv]}


def bad(data, msg):
    with pytest.raises(OperantError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: gather the credited changes per consequence into lists, then average."""
    iv = x["intervals"]
    got = {"reward": [], "punish": [], "none": []}
    for a, b in zip(iv, iv[1:]):
        got[a[1]].append(b[0] - a[0])
    return {k: (len(v), F(sum(v), len(v))) for k, v in got.items() if v}


def check(x):
    o = run(x)
    exp = oracle(x)
    assert {k: (e["transitions"], F(e["mean_change"])) for k, e in o["effects"].items()} == exp
    assert list(o["effects"]) == sorted(o["effects"])
    assert o["increasing"] == sorted(k for k in exp if exp[k][1] > 0)
    assert o["decreasing"] == sorted(k for k in exp if exp[k][1] < 0)
    return o


def test_hand_worked():
    o = run(d())
    assert o["effects"] == {
        "none": {"transitions": 1, "mean_change": "0"},
        "punish": {"transitions": 1, "mean_change": "-4"},
        "reward": {"transitions": 2, "mean_change": "5/2"},
    }
    assert o["increasing"] == ["reward"] and o["decreasing"] == ["punish"]
    assert o["status"] == "completed"
    assert o["claims"] == {"real_behaviour": False, "caused": False, "right_window": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([(5, "none"), (5, "none")]))
    assert o["effects"] == {"none": {"transitions": 1, "mean_change": "0"}} and o["increasing"] == [] and o["decreasing"] == []
    o = run(d([(0, "reward"), (1, "punish")]))
    assert list(o["effects"]) == ["reward"]  # last interval's consequence is not credited
    o = run(d([(0, "reward"), (1, "reward"), (3, "reward")]))
    assert o["effects"]["reward"] == {"transitions": 2, "mean_change": "3/2"}
    o = run(d([(50, "punish"), (0, "none")]))
    assert o["effects"]["punish"]["mean_change"] == "-50" and o["decreasing"] == ["punish"]
    o = run(d([(1, "none"), (2, "punish"), (0, "none"), (1, "none")]))
    assert o["effects"]["none"] == {"transitions": 2, "mean_change": "1"} and o["decreasing"] == ["punish"] and o["increasing"] == ["none"]
    assert o["effects"]["punish"]["mean_change"] == "-2"


def test_random():
    rng = random.Random(893)
    for _ in range(500):
        check(d([(rng.randint(0, 6), rng.choice(("reward", "punish", "none"))) for _ in range(rng.randint(2, 12))]))


def test_caps():
    run(d([(1, "none")] * 12))
    bad(d([(1, "none")] * 13), NI)
    bad(d([(1, "none")] * 10**5), NI)
    bad(d([(1, "none")]), NI)
    bad(d([]), NI)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, (([1, "none"], [2, "none"]))])
def test_noncontainers(v):
    bad({"intervals": v}, NI)


@pytest.mark.parametrize("s", [None, 1, "ab", [1], [1, "none", 2], [], (1, "none"), {}, True])
def test_bad_interval(s):
    x = d()
    x["intervals"][1] = s
    bad(x, EI)


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint_count(s):
    x = d()
    x["intervals"][2][0] = s
    bad(x, "count must be an int")


@pytest.mark.parametrize("s", [-1, 51, 10**30, -(10**30)])
def test_count_range(s):
    x = d()
    x["intervals"][0][0] = s
    bad(x, "count must be 0 to 50")


@pytest.mark.parametrize("s", [0, 50])
def test_count_edges(s):
    check(d([(s, "reward"), (50 - s, "none")]))


@pytest.mark.parametrize("s", ["", "Reward", "reward ", "x", None, 1, True, b"reward", ["reward"]])
def test_bad_consequence(s):
    x = d()
    x["intervals"][1][1] = s
    bad(x, CK)


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("intervals", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    bad({}, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["real_world"] = True
    a["effects"]["reward"]["transitions"] = 99
    a["increasing"].append("zz")
    c = run(x)
    assert c["claims"]["real_world"] is False and c["effects"]["reward"]["transitions"] == 2 and c["increasing"] == ["reward"]
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
    base = {"intervals": [[2, "reward"], [6, "reward"], [7, "punish"], [3, "none"], [3, "reward"]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(OperantError) as e:
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
    base = {"intervals": [[2, "reward"], [6, "reward"], [7, "punish"], [3, "none"], [3, "reward"]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(OperantError):
            run(y)
    assert n >= 4
