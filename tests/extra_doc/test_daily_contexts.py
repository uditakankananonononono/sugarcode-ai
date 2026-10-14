import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import daily_contexts as m
from sugarcode.extra_doc.daily_contexts import ContextError, daily_contexts as run

KEYS = "data keys must be exactly moments"
NM = "moments must be a list of 1 to 12 moments"
EM = "each moment must be a list of [context, minutes]"
CX = "context must be one of home, work, commute, social, online"
ORDER = ["home", "work", "commute", "social", "online"]


def d(mo=(("online", 30), ("home", 10), ("online", 20), ("work", 40))):
    return {"moments": [list(e) for e in mo]}


def bad(data, msg):
    with pytest.raises(ContextError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: per-context filter sums; top via sort on (-minutes, ORDER index)."""
    mo = x["moments"]
    mins = {c: sum(m_ for k, m_ in mo if k == c) for c in ORDER if any(k == c for k, _ in mo)}
    total = sum(m_ for _, m_ in mo)
    top = sorted(mins, key=lambda c: (-mins[c], ORDER.index(c)))[0]
    return mins, total, top, [c for c in ORDER if c not in mins]


def check(x):
    o = run(x)
    mins, total, top, missing = oracle(x)
    assert o["minutes"] == mins and list(o["minutes"]) == list(mins) and o["total"] == total
    assert {c: F(v) for c, v in o["shares"].items()} == {c: F(v, total) for c, v in mins.items()}
    assert list(o["shares"]) == list(mins) and o["top"] == top and o["missing"] == missing
    return o


def test_hand_worked():
    o = run(d())
    assert o["minutes"] == {"home": 10, "work": 40, "online": 50} and o["total"] == 100
    assert o["shares"] == {"home": "1/10", "work": "2/5", "online": "1/2"}
    assert o["top"] == "online" and o["missing"] == ["commute", "social"]
    assert o["status"] == "completed"
    assert o["claims"] == {"happened": False, "minutes_are_learning": False, "contexts_cover_life": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([("online", 5), ("home", 5)]))
    assert o["top"] == "home"  # tie goes to the earlier context in the order
    o = run(d([("social", 5), ("commute", 5)]))
    assert o["top"] == "commute"
    o = run(d([("social", 6), ("commute", 5)]))
    assert o["top"] == "social"
    o = run(d([("work", 120)] * 12))
    assert o["total"] == 1440 and o["shares"] == {"work": "1"} and o["missing"] == ["home", "commute", "social", "online"]
    o = run(d([("commute", 1)]))
    assert o["top"] == "commute" and o["minutes"] == {"commute": 1}
    o = run(d([(c, 1) for c in ORDER]))
    assert o["top"] == "home" and o["missing"] == [] and o["shares"]["online"] == "1/5"


def test_random():
    rng = random.Random(911)
    for _ in range(600):
        check(d([(rng.choice(ORDER), rng.randint(1, 9)) for _ in range(rng.randint(1, 12))]))


def test_caps():
    run(d([("home", 1)] * 12))
    bad(d([("home", 1)] * 13), NM)
    bad(d([("home", 1)] * 10**5), NM)
    bad(d([]), NM)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, ((["home", 1]),)])
def test_noncontainers(v):
    bad({"moments": v}, NM)


@pytest.mark.parametrize("s", [None, 1, "ab", ["home"], ["home", 1, 1], [], ("home", 1), {}, True])
def test_bad_moment(s):
    x = d()
    x["moments"][1] = s
    bad(x, EM)


@pytest.mark.parametrize("s", ["", "Home", "home ", "x", "home-work", None, 1, True, b"home", ["home"]])
def test_bad_context(s):
    x = d()
    x["moments"][1][0] = s
    bad(x, CX)


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint_minutes(s):
    x = d()
    x["moments"][2][1] = s
    bad(x, "minutes must be an int")


@pytest.mark.parametrize("s", [0, 121, -1, 10**30, -(10**30)])
def test_minutes_range(s):
    x = d()
    x["moments"][0][1] = s
    bad(x, "minutes must be 1 to 120")


@pytest.mark.parametrize("s", [1, 120])
def test_minutes_edges(s):
    check(d([("home", s), ("work", 121 - s)]))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("moments", 1)]])
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
    a["minutes"]["home"] = 99
    a["missing"].append("zz")
    c = run(x)
    assert c["claims"]["real_world"] is False and c["minutes"]["home"] == 10 and c["missing"] == ["commute", "social"]
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
    base = {"moments": [["online", 30], ["home", 10], ["online", 20], ["work", 40]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(ContextError) as e:
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
    base = {"moments": [["online", 30], ["home", 10], ["online", 20], ["work", 40]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(ContextError):
            run(y)
    assert n >= 2
