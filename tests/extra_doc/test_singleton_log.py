import re
import pytest
from sugarcode.extra_doc import singleton_log as sl

R = sl.replay
NC = ("an implementation of the pattern", "thread safety", "object creation",
      "design quality", "runtime behaviour")
NM = "name of a-z, 0-9, _ (1 to 30, starting with a letter) required"


class Li(list):
    pass


class Tu(tuple):
    pass


class St(str):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        R(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def test_constants():
    assert sl.MAX_EVENTS == 100 and sl.ACTIONS == ("create", "get") and sl.NOT_CLAIMED == NC


def test_hand_literals():
    r = R([("db", "get"), ("db", "create"), ("db", "get"), ("db", "create"), ("log", "create"), ("db", "create")])
    assert r["created_keys"] == ["db", "log"]
    assert r["violations"] == [(0, "get_before_create"), (3, "duplicate_create"), (5, "duplicate_create")]
    assert r["single_instance_holds"] is False
    r = R([("a", "create"), ("b", "create"), ("a", "get"), ("b", "get")])
    assert r["violations"] == [] and r["single_instance_holds"] is True and r["created_keys"] == ["a", "b"]
    assert R([("a", "get")])["violations"] == [(0, "get_before_create")]
    assert R([("b", "create"), ("a", "create")])["created_keys"] == ["b", "a"]


def test_shape_and_untouched():
    e = [("a", "create")]
    r = R(e)
    assert e == [("a", "create")]
    assert r == {"created_keys": ["a"], "violations": [], "single_instance_holds": True,
                 "singleton_validated": False, "not_claimed": NC}


def test_independent_oracle():
    import random
    rnd = random.Random(666)
    for _ in range(200):
        ev = [(rnd.choice("abc"), rnd.choice(["create", "get"])) for _ in range(rnd.randint(1, 15))]
        want, seen_count = [], {}
        for i, (k, a) in enumerate(ev):
            before = seen_count.get(k, 0)
            if a == "create":
                seen_count[k] = before + 1
                if before:
                    want.append((i, "duplicate_create"))
            elif not before:
                want.append((i, "get_before_create"))
        r = R(ev)
        assert r["violations"] == want
        assert r["created_keys"] == sorted(seen_count, key=lambda k: next(i for i, e in enumerate(ev) if e == (k, "create")))


def test_caps_accepted():
    assert len(R([("a", "get")] * 100)["violations"]) == 100
    assert R([("a" * 30, "create")])["created_keys"] == ["a" * 30]


BAD = [None, 5, "", "A", "1a", "_a", "a-b", "a\n", "\u00e9", "a\u00e9", "\uff41", "a" * 31, St("a"), b"a"]


@pytest.mark.parametrize("bad", BAD)
def test_key_refusals(bad):
    refuse(f"events[0] key: {NM}", [(bad, "get")])
    refuse(f"events[1] key: {NM}", [("a", "get"), (bad, "create")])


@pytest.mark.parametrize("bad", [None, 1, "", "Create", "GET", "create ", "make", "\u0441reate", "get\n", St("get"), b"get"])
def test_action_refusals(bad):
    refuse("events[0] action: 'create' or 'get' required", [("a", bad)])
    refuse("events[1] action: 'create' or 'get' required", [("a", "get"), ("a", bad)])


@pytest.mark.parametrize("bad", [[], ("a",), ("a", "get", 1), Tu(("a", "get")), ["a", "get"], None, "ab"])
def test_event_shape(bad):
    refuse("events[0]: (key, action) tuple required", [bad])
    refuse("events[1]: (key, action) tuple required", [("a", "get"), bad])


@pytest.mark.parametrize("bad", [(), None, "ab", Li([("a", "get")]), [], [("a", "get")] * 101])
def test_events_shape(bad):
    refuse("events: list of 1 to 100 required", bad)


def test_check_order():
    refuse("events[0]: (key, action) tuple required", [None, ("A", "bad")])
    refuse("events[0] key: name of a-z, 0-9, _ (1 to 30, starting with a letter) required", [("A", "bad")])
