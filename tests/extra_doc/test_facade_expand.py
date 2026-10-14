import re
import pytest
from sugarcode.extra_doc import facade_expand as fe

E = fe.expand
NC = ("an implementation of the pattern", "design quality", "runtime behaviour",
      "performance gain", "interface stability")
NM = "name of a-z, 0-9, _ (1 to 30, starting with a letter) required"
SUB = ["open", "read", "close"]
FAC = {"load": ["open", "read", "close"], "peek": ["open", "read"]}


class Li(list):
    pass


class Di(dict):
    pass


class St(str):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        E(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def test_constants():
    assert (fe.MAX_SUB, fe.MAX_FACADE, fe.MAX_STEPS, fe.MAX_CALLS) == (32, 16, 8, 100) and fe.NOT_CLAIMED == NC


def test_hand_literals():
    r = E(SUB, FAC, ["load", "peek", "load"])
    assert r["subsystem_calls"] == ["open", "read", "close", "open", "read", "open", "read", "close"]
    assert (r["subsystem_call_count"], r["facade_call_count"], r["calls_saved"]) == (8, 3, 5)
    r = E(["a"], {"f": ["a", "a"]}, ["f"])
    assert r["subsystem_calls"] == ["a", "a"] and r["calls_saved"] == 1
    r = E(["a"], {"f": ["a"]}, ["f", "f"])
    assert r["calls_saved"] == 0 and r["subsystem_call_count"] == 2


def test_shape_and_inputs_untouched():
    s, f, c = list(SUB), {k: list(v) for k, v in FAC.items()}, ["peek"]
    r = E(s, f, c)
    assert (s, f, c) == (SUB, FAC, ["peek"])
    assert r == {"subsystem_calls": ["open", "read"], "subsystem_call_count": 2, "facade_call_count": 1,
                 "calls_saved": 1, "facade_validated": False, "not_claimed": NC}


def test_independent_oracle():
    import random
    rnd = random.Random(662)
    names = [f"op{i}" for i in range(10)]
    for _ in range(100):
        sub = rnd.sample(names, rnd.randint(1, 10))
        fac = {f"f{j}": [rnd.choice(sub) for _ in range(rnd.randint(1, 8))] for j in range(rnd.randint(1, 5))}
        calls = [rnd.choice(sorted(fac)) for _ in range(rnd.randint(1, 20))]
        want = []
        for c in calls:
            want.extend(fac[c])
        r = E(sub, fac, calls)
        assert r["subsystem_calls"] == want and r["subsystem_call_count"] == len(want)
        assert r["calls_saved"] == len(want) - len(calls)


def test_caps_accepted():
    sub = [f"s{i}" for i in range(32)]
    fac = {f"f{i}": ["s0"] * 8 for i in range(16)}
    r = E(sub, fac, ["f0"] * 100)
    assert r["subsystem_call_count"] == 800 and r["calls_saved"] == 700
    assert E(["a" * 30], {"b" * 30: ["a" * 30]}, ["b" * 30])["facade_call_count"] == 1


BAD_NAMES = [None, 5, "", "A", "1a", "_a", "a-b", "a b", "a\n", "\u00e9", "a\u00e9", "\uff41", "a" * 31, St("a"), b"a"]


@pytest.mark.parametrize("bad", BAD_NAMES)
def test_name_refusals_every_slot(bad):
    refuse(f"subsystem[0]: {NM}", [bad], FAC, ["load"])
    refuse(f"subsystem[1]: {NM}", ["open", bad], FAC, ["load"])
    refuse(f"facade key: {NM}", SUB, {bad: ["open"]}, ["load"])
    refuse(f"facade[load][0]: {NM}", SUB, {"load": [bad]}, ["load"])
    refuse(f"facade[load][1]: {NM}", SUB, {"load": ["open", bad]}, ["load"])
    refuse(f"calls[0]: {NM}", SUB, FAC, [bad])
    refuse(f"calls[1]: {NM}", SUB, FAC, ["load", bad])


@pytest.mark.parametrize("bad", [(), None, "ab", Li(["a"]), [], ["a"] * 33])
def test_subsystem_shape(bad):
    refuse("subsystem: list of 1 to 32 required", bad, FAC, ["load"])


def test_subsystem_distinct():
    refuse("subsystem: names must be distinct", ["open", "read", "open"], FAC, ["load"])


@pytest.mark.parametrize("bad", [None, [], Di({"load": ["open"]}), {}, {f"f{i}": ["open"] for i in range(17)}])
def test_facade_shape(bad):
    refuse("facade: dict of 1 to 16 required", SUB, bad, ["load"])


@pytest.mark.parametrize("bad", [(), None, "open", Li(["open"]), [], ["open"] * 9])
def test_steps_shape(bad):
    refuse("facade[load]: list of 1 to 8 required", SUB, {"load": bad}, ["load"])
    refuse("facade[peek]: list of 1 to 8 required", SUB, {"load": ["open"], "peek": bad}, ["load"])


def test_unknown_names():
    refuse("facade[load][0]: not a subsystem name", SUB, {"load": ["nope"]}, ["load"])
    refuse("facade[load][1]: not a subsystem name", SUB, {"load": ["open", "nope"]}, ["load"])
    refuse("calls[0]: not a facade name", SUB, FAC, ["nope"])
    refuse("calls[2]: not a facade name", SUB, FAC, ["load", "peek", "open"])


@pytest.mark.parametrize("bad", [(), None, "load", Li(["load"]), [], ["load"] * 101])
def test_calls_shape(bad):
    refuse("calls: list of 1 to 100 required", SUB, FAC, bad)


def test_check_order():
    refuse("subsystem: list of 1 to 32 required", None, None, None)
    refuse("facade: dict of 1 to 16 required", SUB, None, None)
    refuse("calls: list of 1 to 100 required", SUB, FAC, None)
    refuse("subsystem: names must be distinct", ["a", "a"], None, None)
