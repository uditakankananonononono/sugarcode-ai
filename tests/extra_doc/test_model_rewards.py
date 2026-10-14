import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import model_rewards as m
from sugarcode.extra_doc.model_rewards import ModelError, model_rewards as run

KEYS = "data keys must be exactly choices, observed"
NO = "observed must be a list of 1 to 12 observations"
NC = "choices must be a list of 1 to 8 action names"
EO = "each observation must be a list of [action, reward]"
AN = "action must be 1..12 characters from a-z and _"


def d(ob=(("push", 4), ("pull", -2), ("push", 1), ("pull", 5)), ch=("push", "pull", "push")):
    return {"observed": [list(e) for e in ob], "choices": list(ch)}


def bad(data, msg):
    with pytest.raises(ModelError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: per-action filter lists; best by sorting on (-mean, name)."""
    ob = x["observed"]
    names = sorted({a for a, _ in ob})
    means = {n: F(sum(r for a, r in ob if a == n), len([1 for a, _ in ob if a == n])) for n in names}
    best = sorted(names, key=lambda n: (-means[n], n))[0]
    f = len([c for c in x["choices"] if c == best])
    return means, best, f, F(f, len(x["choices"]))


def check(x):
    o = run(x)
    means, best, f, rate = oracle(x)
    assert {k: F(v) for k, v in o["means"].items()} == means and list(o["means"]) == sorted(means)
    assert (o["best"], o["followed"], F(o["follow_rate"])) == (best, f, rate)
    return o


def test_hand_worked():
    o = run(d())
    assert o["means"] == {"pull": "3/2", "push": "5/2"} and o["best"] == "push"
    assert o["followed"] == 2 and o["follow_rate"] == "2/3"
    assert o["status"] == "completed"
    assert o["claims"] == {"observer_saw": False, "learned_from_model": False, "comparable_rewards": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([("b", 1), ("a", 1)], ["a"]))
    assert o["best"] == "a" and o["followed"] == 1 and o["follow_rate"] == "1"
    o = run(d([("a", -10)], ["z", "z"]))
    assert o["best"] == "a" and o["followed"] == 0 and o["follow_rate"] == "0" and o["means"] == {"a": "-10"}
    o = run(d([("a", 1), ("a", 2), ("b", 2)], ["b"]))
    assert o["means"] == {"a": "3/2", "b": "2"} and o["best"] == "b"
    o = run(d([("a", 10), ("a", -10), ("b", 0)], ["a", "b"]))
    assert o["best"] == "a" and o["followed"] == 1  # tie 0 vs 0 goes to a


def test_random():
    rng = random.Random(894)
    for _ in range(500):
        ob = [(rng.choice("abcd"), rng.randint(-3, 3)) for _ in range(rng.randint(1, 12))]
        ch = [rng.choice("abcde") for _ in range(rng.randint(1, 8))]
        check(d(ob, ch))


def test_caps():
    run(d([("a", 1)] * 12, ["a"] * 8))
    bad(d([("a", 1)] * 13), NO)
    bad(d([("a", 1)] * 10**5), NO)
    bad(d([]), NO)
    bad(d(ch=["a"] * 9), NC)
    bad(d(ch=["a"] * 10**5), NC)
    bad(d(ch=[]), NC)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, (("a", 1),)])
def test_noncontainers(v):
    x = d()
    x["observed"] = v
    bad(x, NO)
    x = d()
    x["choices"] = v
    bad(x, NC)


@pytest.mark.parametrize("s", [None, 1, "ab", ["a"], ["a", 1, 2], [], ("a", 1), {}, True])
def test_bad_observation(s):
    x = d()
    x["observed"][1] = s
    bad(x, EO)


@pytest.mark.parametrize("s", ["", "A", "a1", "a-b", "a b", "a" * 13, "é", "a\n", None, 1, True, b"a", ["a"]])
def test_bad_action(s):
    bad(d(ob=[(s, 1)]), AN)
    bad(d(ch=[s]), AN)
    bad(d(ch=["a", s]), AN)


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint_reward(s):
    x = d()
    x["observed"][2][1] = s
    bad(x, "reward must be an int")


@pytest.mark.parametrize("s", [-11, 11, 10**30, -(10**30)])
def test_reward_range(s):
    x = d()
    x["observed"][0][1] = s
    bad(x, "reward must be -10 to 10")


@pytest.mark.parametrize("s", [-10, 10])
def test_reward_edges(s):
    check(d([("a", s)], ["a"]))


@pytest.mark.parametrize("s", ["a", "z", "_", "a" * 12])
def test_good_action(s):
    check(d([(s, 1)], [s]))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("observed", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("observed", "choices"):
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
    a["means"]["push"] = "zz"
    c = run(x)
    assert c["claims"]["real_world"] is False and c["means"]["push"] == "5/2"
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
    base = {"observed": [["push", 4], ["pull", -2], ["push", 1], ["pull", 5]], "choices": ["push", "pull", "push"]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(ModelError) as e:
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
    base = {"observed": [["push", 4], ["pull", -2], ["push", 1], ["pull", 5]], "choices": ["push", "pull", "push"]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(ModelError):
            run(y)
    assert n >= 4
