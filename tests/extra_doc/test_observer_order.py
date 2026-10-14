import re
import pytest
from sugarcode.extra_doc import observer_order as oo

N = oo.notify
NC = ("an implementation of the pattern", "callback execution", "thread safety",
      "delivery guarantees", "design quality")
NM = "name of a-z, 0-9, _ (1 to 30, starting with a letter) required"
SUBS = [("a", "t", 0), ("b", "t", 5), ("c", "u", 5), ("d", "t", 5)]


class I(int):
    pass


class Li(list):
    pass


class Tu(tuple):
    pass


class St(str):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        N(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def test_constants():
    assert (oo.MAX_SUBS, oo.MAX_EVENTS) == (32, 50) and oo.NOT_CLAIMED == NC


def test_hand_literals():
    r = N(SUBS, ["t", "u", "x", "t"])
    # topic t: b(5), d(5) tie by registration, then a(0)
    assert r["deliveries"] == [(0, "b"), (0, "d"), (0, "a"), (1, "c"), (3, "b"), (3, "d"), (3, "a")]
    assert r["unobserved_events"] == [2]
    assert N([("a", "t", -100), ("b", "t", 100)], ["t"])["deliveries"] == [(0, "b"), (0, "a")]
    assert N([("a", "t", 3), ("b", "t", 3)], ["t"])["deliveries"] == [(0, "a"), (0, "b")]
    assert N([("b", "t", 3), ("a", "t", 3)], ["t"])["deliveries"] == [(0, "b"), (0, "a")]   # registration, not name


def test_shape_and_untouched():
    s = list(SUBS)
    r = N(s, ["u"])
    assert s == SUBS
    assert r == {"deliveries": [(0, "c")], "unobserved_events": [], "observer_validated": False, "not_claimed": NC}


def test_independent_oracle():
    import random
    rnd = random.Random(663)
    for _ in range(150):
        subs = [(f"n{i}", rnd.choice("tuv"), rnd.randint(-3, 3)) for i in range(rnd.randint(1, 8))]
        events = [rnd.choice("tuvw") for _ in range(rnd.randint(1, 10))]
        want = []
        for e, topic in enumerate(events):
            bucket = [(p, i, n) for i, (n, t, p) in enumerate(subs) if t == topic]
            bucket.sort(key=lambda x: (-x[0], x[1]))
            want += [(e, n) for _, _, n in bucket]
        r = N(subs, events)
        assert r["deliveries"] == want
        assert r["unobserved_events"] == [e for e, t in enumerate(events) if not any(s[1] == t for s in subs)]


def test_caps_accepted():
    subs = [(f"s{i}", "t", i) for i in range(32)]
    assert len(N(subs, ["t"] * 50)["deliveries"]) == 32 * 50
    assert N([("a" * 30, "b" * 30, 100)], ["b" * 30])["deliveries"] == [(0, "a" * 30)]


BAD = [None, 5, "", "A", "1a", "_a", "a-b", "a\n", "\u00e9", "a\u00e9", "\uff41", "a" * 31, St("a"), b"a"]


@pytest.mark.parametrize("bad", BAD)
def test_name_refusals(bad):
    refuse(f"subscriptions[0] name: {NM}", [(bad, "t", 0)], ["t"])
    refuse(f"subscriptions[1] name: {NM}", [("a", "t", 0), (bad, "t", 0)], ["t"])
    refuse(f"subscriptions[0] topic: {NM}", [("a", bad, 0)], ["t"])
    refuse(f"subscriptions[1] topic: {NM}", [("a", "t", 0), ("b", bad, 0)], ["t"])
    refuse(f"events[0]: {NM}", SUBS, [bad])
    refuse(f"events[1]: {NM}", SUBS, ["t", bad])


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, I(1), -101, 101])
def test_priority_refusals(bad):
    refuse("subscriptions[0] priority: whole number -100 to 100 required", [("a", "t", bad)], ["t"])
    refuse("subscriptions[1] priority: whole number -100 to 100 required", [("a", "t", 0), ("b", "t", bad)], ["t"])


@pytest.mark.parametrize("bad", [[], ("a", "t"), ("a", "t", 0, 1), Tu(("a", "t", 0)), ["a", "t", 0], None, "abc"])
def test_tuple_shape(bad):
    refuse("subscriptions[0]: (name, topic, priority) tuple required", [bad], ["t"])
    refuse("subscriptions[1]: (name, topic, priority) tuple required", [("a", "t", 0), bad], ["t"])


@pytest.mark.parametrize("bad", [(), None, "ab", Li([("a", "t", 0)]), [], [("a", "t", 0)] * 33])
def test_subscriptions_shape(bad):
    refuse("subscriptions: list of 1 to 32 required", bad, ["t"])


@pytest.mark.parametrize("bad", [(), None, "t", Li(["t"]), [], ["t"] * 51])
def test_events_shape(bad):
    refuse("events: list of 1 to 50 required", SUBS, bad)


def test_distinct_and_order():
    refuse("subscriptions: names must be distinct", [("a", "t", 0), ("a", "u", 1)], ["t"])
    refuse("subscriptions: list of 1 to 32 required", None, None)
    refuse("subscriptions[0]: (name, topic, priority) tuple required", [None, ("a", "t", True)], None)
    refuse("subscriptions: names must be distinct", [("a", "t", 0), ("a", "u", 1)], None)
    refuse("events: list of 1 to 50 required", SUBS, None)
