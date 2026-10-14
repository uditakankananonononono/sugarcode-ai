import copy
import random
import re
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import attention_log as m
from sugarcode.extra_doc.attention_log import AttentionError, attention_log as run

KEYS = "data keys must be exactly checkins"
LEN = "checkins must be a string of 1..500 characters"


def bad(data, msg):
    with pytest.raises(AttentionError) as e:
        run(data)
    assert str(e.value) == msg


def check(s):
    """Independent: regex runs and overlapping-pattern counts."""
    o = run({"checkins": s})
    runs = [len(r) for r in re.findall(r"P+", s)]
    assert o["length"] == len(s) and o["present"] == s.count("P") and o["drifted"] == s.count("D")
    assert F(o["present_share"]) == F(s.count("P"), len(s))
    assert o["drifts"] == len(re.findall(r"P(?=D)", s)) and o["returns"] == len(re.findall(r"D(?=P)", s))
    assert o["longest_present_run"] == max(runs, default=0)
    assert (None if not runs else F(o["mean_present_run"])) == (None if not runs else F(sum(runs), len(runs)))
    assert (o["mean_present_run"] is None) == (not runs)
    return o


def test_hand_worked():
    o = run({"checkins": "PPPDDPPDPPPP"})
    assert (o["length"], o["present"], o["drifted"], o["present_share"]) == (12, 9, 3, "3/4")
    assert (o["drifts"], o["returns"], o["longest_present_run"], o["mean_present_run"]) == (2, 2, 4, "3")
    assert o["status"] == "completed"
    assert o["claims"] == {"accurate_checkins": False, "measures_mindfulness": False, "predictive": False, "health_claim": False}
    assert len(o["not_claimed"]) == 4


def test_edges():
    o = check("P")
    assert (o["drifts"], o["returns"], o["mean_present_run"], o["longest_present_run"]) == (0, 0, "1", 1)
    o = check("D")
    assert (o["mean_present_run"], o["longest_present_run"], o["present_share"]) == (None, 0, "0")
    assert check("PD")["drifts"] == 1 and check("DP")["returns"] == 1
    assert check("PDP")["mean_present_run"] == "1"
    assert check("PPD")["mean_present_run"] == "2"      # run closed by a D
    assert check("DPP")["mean_present_run"] == "2"      # run closed by end of string
    assert check("PPDPPPD")["mean_present_run"] == "5/2"
    assert check("DDDD")["drifts"] == 0


def test_random():
    rng = random.Random(806)
    for _ in range(500):
        check("".join(rng.choice("PD") for _ in range(rng.randint(1, 30))))
    check("P" * 500)
    check("D" * 500)
    check("PD" * 250)


def test_caps():
    run({"checkins": "P" * 500})
    bad({"checkins": "P" * 501}, LEN)
    bad({"checkins": "P" * 10**6}, LEN)
    bad({"checkins": ""}, LEN)
    for s in ("PX", "p", "d", "P D", "P\n", "PD1"):
        bad({"checkins": s}, "checkins must use only P and D")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, ["P"], {}, ("P",), b"P"])
def test_nonstring(v):
    bad({"checkins": v}, LEN)


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("checkins", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    bad({}, KEYS)
    bad({"checkins": "P", "x": 1}, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = {"checkins": "PDP"}
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["health_claim"] = True
    a["not_claimed"].append("x")
    r = run(x)
    assert r["claims"]["health_claim"] is False and len(r["not_claimed"]) == 4 and m.CLAIMS["health_claim"] is False


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
    base = {"checkins": "PDP"}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(AttentionError):
            run(y)
    assert n >= 4
