import re
import itertools
import pytest
from sugarcode.extra_doc import tough_topics as tt

P = tt.plan
NC = ("what any topic is", "whether a topic is actually difficult", "how to hold any conversation",
      "whether the packing order is kind or wise", "anyone's emotional state")
TM = "topics: tuple of 0 to 40 entries required"
PM = "per_session: whole number 1 to 10 required"


class I(int):
    pass


class St(str):
    pass


class Tu(tuple):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        P(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def oracle(topics, per):                  # independent: flag list first, then a fresh scan
    flags = [lv in (4, 5) for _, lv in topics]
    out, cur, t = [], [], 0
    for i, (nm, lv) in enumerate(topics):
        if cur and (len(cur) == 12 or (flags[i] and t == per)):
            out.append((tuple(cur), t))
            cur, t = [], 0
        cur.append((i, nm))
        if flags[i]:
            t += 1
    if cur:
        out.append((tuple(cur), t))
    return out


def test_constants():
    assert (tt.MAX_TOPICS, tt.MAX_NAME, tt.MAX_LEVEL, tt.TOUGH_AT, tt.MAX_PER_SESSION, tt.MAX_SESSION) == \
        (40, 40, 5, 4, 10, 12) and tt.NOT_CLAIMED == NC


def test_literals():
    r = P((("a", 1), ("b", 4), ("c", 5), ("d", 1)), 1)
    assert r == {"sessions": (((0, "a"), (1, "b")), ((2, "c"), (3, "d"))), "tough": (1, 1),
                 "tough_topics_validated": False, "not_claimed": NC}
    assert P((), 5) == {"sessions": (), "tough": (), "tough_topics_validated": False, "not_claimed": NC}
    assert P((("x", 4),), 1)["tough"] == (1,)
    assert P((("a", 3), ("b", 3)), 1)["sessions"] == (((0, "a"), (1, "b")),)
    assert P((("a", 3), ("b", 3)), 1)["tough"] == (0,)
    r = P((("caf\u00e9", 4), ("x\uff41", 1), ("a\n", 1)), 2)
    assert r["sessions"] == (((0, "caf\u00e9"), (1, "x\uff41"), (2, "a\n")),) and r["tough"] == (1,)


def test_oracle_exhaustive():
    for n in range(5):
        for combo in itertools.product((1, 3, 4, 5), repeat=n):
            topics = tuple((chr(97 + i), lv) for i, lv in enumerate(combo))
            for per in (1, 2, 3):
                r = P(topics, per)
                o = oracle(topics, per)
                assert r["sessions"] == tuple(s for s, _ in o) and r["tough"] == tuple(t for _, t in o)


def test_caps_and_edges():
    big = tuple(("t%d" % i, 1) for i in range(40))
    r = P(big, 5)
    assert tuple(len(s) for s in r["sessions"]) == (12, 12, 12, 4) and r["tough"] == (0, 0, 0, 0)
    refuse(TM, tuple(("t%d" % i, 1) for i in range(41)), 5)
    assert P((("n" * 40, 5),), 1)["sessions"] == (((0, "n" * 40),),)
    refuse("topics[0] name: str of 1 to 40 characters required", (("n" * 41, 5),), 1)
    refuse("topics[0] name: str of 1 to 40 characters required", (("", 5),), 1)
    for per in (1, 10):
        assert P((("x", 4),), per)["tough"] == (1,)
    refuse(PM, (("x", 4),), 0)
    refuse(PM, (("x", 4),), 11)


def test_boundary_positions():
    r = P(tuple(("t%d" % i, 4) for i in range(12)), 10)     # tough cap: 11th tough topic splits
    assert tuple(len(s) for s in r["sessions"]) == (10, 2) and r["tough"] == (10, 2)
    r = P(tuple(("t%d" % i, 4) for i in range(11)), 10)
    assert tuple(len(s) for s in r["sessions"]) == (10, 1) and r["tough"] == (10, 1)
    r = P(tuple(("t%d" % i, 4) for i in range(10)), 10)     # exactly at the cap: no split
    assert r["sessions"] == (tuple((i, "t%d" % i) for i in range(10)),) and r["tough"] == (10,)
    r = P((("h", 4),) + tuple(("t%d" % i, 1) for i in range(12)), 1)   # tough first, size fills: 13th splits
    assert tuple(len(s) for s in r["sessions"]) == (12, 1) and r["tough"] == (1, 0)
    r = P(tuple(("t%d" % i, 1) for i in range(11)) + (("last", 4),), 1)  # tough at last position
    assert r["sessions"][-1] == tuple(list((i, "t%d" % i) for i in range(11)) + [(11, "last")])
    assert r["tough"] == (1,)
    r = P((("a", 4), ("b", 4)), 1)                          # tough at first position forces the second out
    assert r["sessions"] == (((0, "a"),), ((1, "b"),)) and r["tough"] == (1, 1)
    r = P((("a", 1), ("b", 4), ("c", 4), ("d", 1)), 2)      # two tough fit: no split
    assert r["sessions"] == (((0, "a"), (1, "b"), (2, "c"), (3, "d")),) and r["tough"] == (2,)
    r = P((("a", 5), ("b", 4)), 1)                          # level 5 is tough too
    assert r["tough"] == (1, 1)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, I(1), 0, 6, -1])
def test_level(bad):
    refuse("topics[0] level: whole number 1 to 5 required", (("a", bad),), 5)
    refuse("topics[2] level: whole number 1 to 5 required", (("a", 1), ("b", 1), ("c", bad)), 5)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, I(1), 0, 11, -1])
def test_per_session(bad):
    refuse(PM, (("a", 1),), bad)


@pytest.mark.parametrize("bad", [[], [("a", 1)], None, "x", 5, Tu((("a", 1),))])
def test_topics_shape(bad):
    refuse(TM, bad, 5)


@pytest.mark.parametrize("bad", [None, 5, St("a"), b"a"])
def test_name(bad):
    refuse("topics[0] name: str of 1 to 40 characters required", ((bad, 1),), 5)
    refuse("topics[1] name: str of 1 to 40 characters required", (("a", 1), (bad, 1)), 5)


@pytest.mark.parametrize("bad", [("a",), ("a", 1, 2), ["a", 1], Tu(("a", 1)), None, "ab"])
def test_entry_shape(bad):
    refuse("topics[0]: (name, level) tuple required", (bad,), 5)
    refuse("topics[1]: (name, level) tuple required", (("a", 1), bad), 5)


def test_order():
    refuse(TM, None, None)                                   # topics shape before per_session
    refuse(PM, (("a", 0),), 0)                               # per_session before entry checks
    refuse("topics[1] level: whole number 1 to 5 required", (("a", 1), ("b", 0)), 5)
    refuse("topics[0]: (name, level) tuple required", (("a",), ("b", 0)), 5)
    refuse("topics[0] name: str of 1 to 40 characters required", ((1, 0),), 5)
