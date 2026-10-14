import copy
import random

import pytest

from sugarcode.extra_doc import vicarious_tally as m
from sugarcode.extra_doc.vicarious_tally import VicariousError, vicarious_tally as run

KEYS = "data keys must be exactly seen"
NS = "seen must be a list of 1 to 12 observations"
ES = "each observation must be a list of [action, outcome]"
AN = "action must be 1..12 characters from a-z and _"
OC = "outcome must be reward or punish"


def d(seen=(("a", "reward"), ("b", "punish"), ("a", "reward"), ("c", "reward"), ("c", "punish"))):
    return {"seen": [list(e) for e in seen]}


def bad(data, msg):
    with pytest.raises(VicariousError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: signed sum per action (+1 reward, -1 punish) and separate counts via filters."""
    s = x["seen"]
    acts = sorted({a for a, _ in s})
    rows = {}
    for a in acts:
        r = len([1 for b, o in s if b == a and o == "reward"])
        p = len([1 for b, o in s if b == a and o == "punish"])
        signed = sum(1 if o == "reward" else -1 for b, o in s if b == a)
        assert signed == r - p
        rows[a] = {"rewards": r, "punishes": p, "net": signed}
    return rows


def check(x):
    o = run(x)
    rows = oracle(x)
    assert o["actions"] == rows and list(o["actions"]) == sorted(rows)
    assert o["approach"] == [a for a in sorted(rows) if rows[a]["net"] > 0]
    assert o["avoid"] == [a for a in sorted(rows) if rows[a]["net"] < 0]
    assert o["neutral"] == [a for a in sorted(rows) if rows[a]["net"] == 0]
    return o


def test_hand_worked():
    o = run(d())
    assert o["actions"] == {
        "a": {"rewards": 2, "punishes": 0, "net": 2},
        "b": {"rewards": 0, "punishes": 1, "net": -1},
        "c": {"rewards": 1, "punishes": 1, "net": 0},
    }
    assert o["approach"] == ["a"] and o["avoid"] == ["b"] and o["neutral"] == ["c"]
    assert o["status"] == "completed"
    assert o["claims"] == {"observer_saw": False, "decides_choice": False, "equal_weight": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([("z", "punish")]))
    assert o["avoid"] == ["z"] and o["approach"] == [] and o["neutral"] == []
    o = run(d([("z", "reward")]))
    assert o["approach"] == ["z"] and o["avoid"] == [] and o["neutral"] == []
    o = run(d([("b", "reward"), ("a", "reward")]))
    assert list(o["actions"]) == ["a", "b"] and o["approach"] == ["a", "b"]


def test_random():
    rng = random.Random(896)
    for _ in range(500):
        check(d([(rng.choice("abcd"), rng.choice(("reward", "punish"))) for _ in range(rng.randint(1, 12))]))


def test_caps():
    run(d([("a", "reward")] * 12))
    bad(d([("a", "reward")] * 13), NS)
    bad(d([("a", "reward")] * 10**5), NS)
    bad(d([]), NS)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, (("a", "reward"),)])
def test_noncontainers(v):
    bad({"seen": v}, NS)


@pytest.mark.parametrize("s", [None, 1, "ab", ["a"], ["a", "reward", 1], [], ("a", "reward"), {}, True])
def test_bad_observation(s):
    x = d()
    x["seen"][1] = s
    bad(x, ES)


@pytest.mark.parametrize("s", ["", "A", "a1", "a-b", "a b", "a" * 13, "é", "a\n", None, 1, True, b"a", ["a"]])
def test_bad_action(s):
    bad(d([(s, "reward")]), AN)


@pytest.mark.parametrize("s", ["a", "z", "_", "a" * 12])
def test_good_action(s):
    check(d([(s, "reward")]))


@pytest.mark.parametrize("s", ["", "Reward", "reward ", "x", None, 1, True, b"reward", ["reward"]])
def test_bad_outcome(s):
    bad(d([("a", s)]), OC)


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("seen", 1)]])
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
    a["actions"]["a"]["net"] = 99
    a["approach"].append("zz")
    c = run(x)
    assert c["claims"]["real_world"] is False and c["actions"]["a"]["net"] == 2 and c["approach"] == ["a"]
    assert len(m.NOT_CLAIMED) == 4 and all(v is False for v in m.CLAIMS.values())


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
    base = {"seen": [["a", "reward"], ["b", "punish"], ["a", "reward"]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(VicariousError):
            run(y)
    assert n >= 4
