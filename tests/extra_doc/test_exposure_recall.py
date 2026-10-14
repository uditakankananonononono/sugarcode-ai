import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import exposure_recall as m
from sugarcode.extra_doc.exposure_recall import ExposureError, exposure_recall as run

KEYS = "data keys must be exactly words"
NW = "words must be a list of 1 to 12 words"
EW = "each word must be a list of [word, exposures, recalled]"
WN = "word must be 1..12 characters from a-z and _"


def d(w=(("a", 1, 0), ("b", 2, 1), ("c", 4, 1), ("e", 5, 0), ("f", 9, 1))):
    return {"words": [list(e) for e in w]}


def bad(data, msg):
    with pytest.raises(ExposureError) as e:
        run(data)
    assert str(e.value) == msg


def band_of(x):
    return "low" if x <= 2 else "mid" if x <= 5 else "high"


def oracle(x):
    """Independent: classify each word with band_of, tally in dicts."""
    n = {"low": 0, "mid": 0, "high": 0}
    r = {"low": 0, "mid": 0, "high": 0}
    for _, e, rec in x["words"]:
        b = band_of(e)
        n[b] += 1
        r[b] += rec
    rates = {b: (F(r[b], n[b]) if n[b] else None) for b in n}
    present = [rates[b] for b in ("low", "mid", "high") if rates[b] is not None]
    rising = True
    for a, b in zip(present, present[1:]):
        if b < a:
            rising = False
    return n, r, rates, F(sum(r.values()), len(x["words"])), rising


def check(x):
    o = run(x)
    n, r, rates, overall, rising = oracle(x)
    assert list(o["bands"]) == ["low", "mid", "high"]
    for b in n:
        assert (o["bands"][b]["words"], o["bands"][b]["recalled"]) == (n[b], r[b])
        assert (o["bands"][b]["rate"] is None) == (rates[b] is None)
        if rates[b] is not None:
            assert F(o["bands"][b]["rate"]) == rates[b]
    assert F(o["overall_rate"]) == overall and o["rising"] is rising
    return o


def test_hand_worked():
    o = run(d())
    assert o["bands"] == {
        "low": {"words": 2, "recalled": 1, "rate": "1/2"},
        "mid": {"words": 2, "recalled": 1, "rate": "1/2"},
        "high": {"words": 1, "recalled": 1, "rate": "1"},
    }
    assert o["overall_rate"] == "3/5" and o["rising"] is True
    assert o["status"] == "completed"
    assert o["claims"] == {"happened": False, "caused_recall": False, "right_bands": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_band_edges():
    for x, b in ((1, "low"), (2, "low"), (3, "mid"), (5, "mid"), (6, "high"), (10, "high")):
        o = run(d([("a", x, 1)]))
        assert o["bands"][b]["words"] == 1 and sum(v["words"] for v in o["bands"].values()) == 1


def test_cases():
    o = run(d([("a", 1, 1), ("b", 7, 0)]))
    assert o["rising"] is False and o["bands"]["mid"] == {"words": 0, "recalled": 0, "rate": None}
    o = run(d([("a", 3, 0)]))
    assert o["rising"] is True and o["overall_rate"] == "0"
    o = run(d([("a", 1, 1), ("b", 4, 0), ("c", 8, 1)]))
    assert o["rising"] is False  # 1 -> 0 falls even though high recovers
    o = run(d([("a", 1, 0), ("b", 4, 0), ("c", 8, 0)]))
    assert o["rising"] is True
    o = run(d([("a", 1, 1), ("b", 1, 0), ("c", 9, 1), ("e", 9, 0)]))
    assert o["rising"] is True and o["bands"]["low"]["rate"] == "1/2"


def test_random():
    rng = random.Random(908)
    for _ in range(600):
        names = rng.sample("abcdefghijkl", rng.randint(1, 12))
        check(d([(n, rng.randint(1, 10), rng.randint(0, 1)) for n in names]))


def test_caps():
    names = list("abcdefghijkl")
    run(d([(n, 1, 1) for n in names]))
    bad(d([(n, 1, 1) for n in names] + [("m", 1, 1)]), NW)
    bad(d([("a", 1, 1)] * 10**5), NW)
    bad(d([]), NW)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, ((["a", 1, 1]),)])
def test_noncontainers(v):
    bad({"words": v}, NW)


@pytest.mark.parametrize("s", [None, 1, "ab", ["a"], ["a", 1], ["a", 1, 1, 1], [], ("a", 1, 1), {}, True])
def test_bad_word_row(s):
    x = d()
    x["words"][1] = s
    bad(x, EW)


@pytest.mark.parametrize("s", ["", "A", "a1", "a-b", "a b", "a" * 13, "é", "a\n", None, 1, True, b"a", ["a"]])
def test_bad_word(s):
    bad(d([(s, 1, 1)]), WN)


@pytest.mark.parametrize("s", ["a", "z", "_", "a" * 12])
def test_good_word(s):
    check(d([(s, 1, 1)]))


@pytest.mark.parametrize("s", [True, False, 1.0, "2", None, [1], b"2"])
def test_nonint(s):
    for pos in (1, 2):
        x = d()
        x["words"][1][pos] = s
        bad(x, "exposures and recalled must be ints")


@pytest.mark.parametrize("s", [0, 11, -1, 10**30, -(10**30)])
def test_exposures_range(s):
    x = d()
    x["words"][0][1] = s
    bad(x, "exposures must be 1 to 10")


@pytest.mark.parametrize("s", [2, -1, 10**30])
def test_recalled_range(s):
    x = d()
    x["words"][0][2] = s
    bad(x, "recalled must be 0 or 1")


def test_distinct_words():
    bad(d([("a", 1, 1), ("a", 2, 0)]), "words must be distinct")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("words", 1)]])
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
    a["bands"]["low"]["words"] = 99
    c = run(x)
    assert c["claims"]["real_world"] is False and c["bands"]["low"]["words"] == 2
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
    base = {"words": [["a", 1, 0], ["b", 2, 1], ["c", 4, 1], ["e", 5, 0], ["f", 9, 1]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(ExposureError) as e:
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
    base = {"words": [["a", 1, 0], ["b", 2, 1], ["c", 4, 1], ["e", 5, 0], ["f", 9, 1]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(ExposureError):
            run(y)
    assert n >= 2
