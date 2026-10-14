import copy
import random

import pytest

from sugarcode.extra_doc import autoscale_run as m
from sugarcode.extra_doc.autoscale_run import ScaleError, autoscale_run as run

KEYS = "data keys must be exactly capacity, down_ticks, loads, max_replicas, min_replicas, start"
NL = "loads must be a list of 1 to 20 loads"


def d(loads=(100, 100, 10, 10, 10, 10), cap=50, lo=1, hi=5, start=1, dt=2):
    return {"loads": list(loads), "capacity": cap, "min_replicas": lo, "max_replicas": hi, "start": start, "down_ticks": dt}


def bad(data, msg):
    with pytest.raises(ScaleError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: smallest replica count found by search, state kept as a recent-lows list."""
    cur = x["start"]
    recent = []
    hist, drop, ups, downs = [], [], 0, 0
    for load in x["loads"]:
        need = 1
        while need * x["capacity"] < load:
            need += 1
        need = max(x["min_replicas"], need)
        need = min(x["max_replicas"], need)
        before = cur
        if need > cur:
            cur, recent = need, []
        elif need < cur:
            recent.append(load)
            if len(recent) == x["down_ticks"]:
                cur, recent = cur - 1, []
        else:
            recent = []
        ups += cur > before
        downs += cur < before
        hist.append(cur)
        drop.append(load - cur * x["capacity"] if load > cur * x["capacity"] else 0)
    return hist, drop, ups, downs


def check(x):
    o = run(x)
    h, dr, u, dn = oracle(x)
    assert (o["history"], o["dropped"], o["scale_ups"], o["scale_downs"]) == (h, dr, u, dn)
    assert o["total_dropped"] == sum(dr) and o["peak"] == max(h)
    return o


def test_hand_worked():
    o = run(d())
    assert o["history"] == [2, 2, 2, 1, 1, 1] and o["dropped"] == [0] * 6
    assert o["scale_ups"] == 1 and o["scale_downs"] == 1 and o["peak"] == 2 and o["total_dropped"] == 0
    assert o["status"] == "completed"
    assert o["claims"] == {"real_capacity": False, "good_policy": False, "real_traffic": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cap_clamp_and_drops():
    o = run(d(loads=[300], cap=50, lo=1, hi=3, start=1))
    assert o["history"] == [3] and o["dropped"] == [150] and o["total_dropped"] == 150 and o["scale_ups"] == 1
    o = run(d(loads=[151], cap=50, lo=1, hi=5, start=1))
    assert o["history"] == [4] and o["dropped"] == [0]  # ceil(151/50)=4
    o = run(d(loads=[150], cap=50, lo=1, hi=5, start=1))
    assert o["history"] == [3]  # exactly 3
    o = run(d(loads=[0], cap=50, lo=2, hi=5, start=2))
    assert o["history"] == [2] and o["scale_downs"] == 0 and o["scale_ups"] == 0


def test_floor_min_replicas():
    o = run(d(loads=[10, 10, 10], cap=50, lo=3, hi=5, start=5, dt=1))
    assert o["history"] == [4, 3, 3] and o["scale_downs"] == 2


def test_down_ticks_counter_resets():
    # dt 3: two low ticks, then an equal tick resets, then two more lows: no drop yet
    o = run(d(loads=[100, 10, 10, 100, 10, 10], cap=50, lo=1, hi=5, start=2, dt=3))
    assert o["history"] == [2] * 6 and o["scale_downs"] == 0
    # reset by an upward tick too
    o = run(d(loads=[10, 10, 200, 10, 10, 10], cap=50, lo=1, hi=5, start=2, dt=3))
    assert o["history"] == [2, 2, 4, 4, 4, 3] and o["scale_ups"] == 1 and o["scale_downs"] == 1
    o = run(d(loads=[10, 10, 10, 10], cap=50, lo=1, hi=5, start=3, dt=2))
    assert o["history"] == [3, 2, 2, 1]
    o = run(d(loads=[10] * 6, cap=50, lo=1, hi=5, start=3, dt=1))
    assert o["history"] == [2, 1, 1, 1, 1, 1] and o["scale_downs"] == 2


def test_down_steps_by_one():
    o = run(d(loads=[0, 0], cap=50, lo=1, hi=9, start=9, dt=1))
    assert o["history"] == [8, 7]


def test_dropped_uses_count_after_change():
    o = run(d(loads=[120], cap=50, lo=1, hi=5, start=1))
    assert o["history"] == [3] and o["dropped"] == [0]
    o = run(d(loads=[500, 500], cap=50, lo=1, hi=4, start=4))
    assert o["dropped"] == [300, 300]
    o = run(d(loads=[199], cap=100, lo=1, hi=1, start=1))
    assert o["dropped"] == [99]
    o = run(d(loads=[100], cap=100, lo=1, hi=1, start=1))
    assert o["dropped"] == [0]


def test_random():
    rng = random.Random(520)
    for _ in range(1500):
        lo = rng.randint(1, 20)
        hi = rng.randint(lo, 20)
        n = rng.randint(1, 20)
        cap = rng.randint(1, 1000)
        loads = [rng.choice([0, rng.randint(0, 10000), rng.randint(0, 3) * cap]) for _ in range(n)]
        check(d(loads, cap, lo, hi, rng.randint(lo, hi), rng.randint(1, 5)))


def test_caps():
    run(d(loads=[0] * 20))
    bad(d(loads=[0] * 21), NL)
    bad(d(loads=[0] * 10**5), NL)
    bad(d(loads=[]), NL)


@pytest.mark.parametrize("v", [True, 1, "ab", None, (1, 2), {}])
def test_noncontainers(v):
    x = d()
    x["loads"] = v
    bad(x, NL)


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint(s):
    x = d()
    x["loads"][1] = s
    bad(x, "load must be an int")
    for k in ("capacity", "min_replicas", "max_replicas", "start", "down_ticks"):
        x = d()
        x[k] = s
        bad(x, k + " must be an int")


@pytest.mark.parametrize("s", [-1, 10001, 10**30, -(10**30)])
def test_load_range(s):
    x = d()
    x["loads"][0] = s
    bad(x, "load must be 0 to 10000")


def test_param_ranges():
    for k, lo, hi in (("capacity", 1, 1000), ("down_ticks", 1, 5), ("min_replicas", 1, 20), ("max_replicas", 1, 20)):
        for v in (lo - 1, hi + 1, 10**30, -(10**30)):
            x = d(lo=1, hi=5, start=1)
            x[k] = v
            bad(x, "%s must be %d to %d" % (k, lo, hi))
    run(d(cap=1000, dt=5, lo=20, hi=20, start=20))
    run(d(cap=1, dt=1, lo=1, hi=1, start=1))


def test_min_max_start():
    bad(d(lo=4, hi=3, start=3), "min_replicas must not exceed max_replicas")
    bad(d(lo=2, hi=4, start=1), "start must be 2 to 4")
    bad(d(lo=2, hi=4, start=5), "start must be 2 to 4")
    run(d(lo=2, hi=4, start=2))
    run(d(lo=2, hi=4, start=4))
    run(d(lo=3, hi=3, start=3))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("loads", 1)]])
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
    a["history"][0] = 99
    c = run(x)
    assert c["claims"]["real_world"] is False and c["history"][0] == 2
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
    base = {"loads": [100, 100, 10, 10, 10, 10], "capacity": 50, "min_replicas": 1, "max_replicas": 5, "start": 1, "down_ticks": 2}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(ScaleError) as e:
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
    base = {"loads": [100, 100, 10, 10, 10, 10], "capacity": 50, "min_replicas": 1, "max_replicas": 5, "start": 1, "down_ticks": 2}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(ScaleError):
            run(y)
    assert n >= 2
