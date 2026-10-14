import re
import itertools
import pytest
from sugarcode.extra_doc import constructive_balance as cb

S = cb.sequence
NC = ("whether any note is true", "whether any note is kind", "writing quality of any note",
      "whether the feedback should be given at all", "how anyone will receive it")
SM = "strengths: tuple of 0 to 20 notes required"
IM = "improvements: tuple of 0 to 20 notes required"


class St(str):
    pass


class Tu(tuple):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        S(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def oracle(s, i):                         # independent: zip pairing plus a remainder slice
    out = []
    for k, (a, b) in enumerate(zip(s, i)):
        out += [("strength", k, a), ("improvement", k, b)]
    out += [("strength", k, s[k]) for k in range(len(i), len(s))]
    return out, list(range(len(s), len(i)))


def test_constants():
    assert cb.MAX_NOTES == 20 and cb.MAX_NOTE == 60 and cb.NOT_CLAIMED == NC


def test_literals():
    assert S(("s0", "s1"), ("i0",)) == {
        "sequence": (("strength", 0, "s0"), ("improvement", 0, "i0"), ("strength", 1, "s1")),
        "held": (), "strength_count": 2, "improvement_count": 1,
        "constructive_balance_validated": False, "not_claimed": NC}
    assert S((), ("i0", "i1")) == {"sequence": (), "held": (0, 1), "strength_count": 0, "improvement_count": 2,
                                   "constructive_balance_validated": False, "not_claimed": NC}
    assert S(("s0",), ("i0", "i1", "i2"))["held"] == (1, 2)
    assert S(("s0",), ("i0", "i1", "i2"))["sequence"] == (("strength", 0, "s0"), ("improvement", 0, "i0"))
    assert S(("a",), ())["sequence"] == (("strength", 0, "a"),)
    assert S((), ())["sequence"] == () and S((), ())["held"] == ()
    r = S(("caf\u00e9", "x\uff41"), ("a\n", "b\u0430"))
    assert r["sequence"] == (("strength", 0, "caf\u00e9"), ("improvement", 0, "a\n"),
                             ("strength", 1, "x\uff41"), ("improvement", 1, "b\u0430"))


def test_oracle_exhaustive():
    for ls in range(4):
        for li in range(4):
            for s in itertools.product(("a", "b"), repeat=ls):
                for i in itertools.product(("x", "y"), repeat=li):
                    r = S(s, i)
                    o, h = oracle(s, i)
                    assert r["sequence"] == tuple(o) and r["held"] == tuple(h)
                    assert r["strength_count"] == ls and r["improvement_count"] == li


def test_caps_and_edges():
    s = tuple("s%d" % k for k in range(20))
    i = tuple("i%d" % k for k in range(20))
    r = S(s, i)
    assert len(r["sequence"]) == 40 and r["held"] == ()
    assert r["sequence"][0] == ("strength", 0, "s0") and r["sequence"][-1] == ("improvement", 19, "i19")
    refuse(SM, tuple("s%d" % k for k in range(21)), ())
    refuse(IM, (), tuple("i%d" % k for k in range(21)))
    assert S(("n" * 60,), ())["sequence"] == (("strength", 0, "n" * 60),)
    refuse("strengths[0]: note of 1 to 60 characters required", ("n" * 61,), ())
    refuse("strengths[0]: note of 1 to 60 characters required", ("",), ())
    assert S((), ("m" * 60,))["held"] == (0,)                       # 60-char improvement accepted, then held
    refuse("improvements[0]: note of 1 to 60 characters required", (), ("n" * 61,))
    refuse("improvements[0]: note of 1 to 60 characters required", (), ("",))


def test_boundary_positions():
    r = S(("only",), tuple("i%d" % k for k in range(20)))
    assert r["held"] == tuple(range(1, 20))                   # last held improvement is position 19
    assert r["sequence"] == (("strength", 0, "only"), ("improvement", 0, "i0"))
    r = S(tuple("s%d" % k for k in range(20)), ("one",))
    assert r["sequence"][-1] == ("strength", 19, "s19")       # trailing strength at last position
    assert r["sequence"][:2] == (("strength", 0, "s0"), ("improvement", 0, "one"))
    r = S(("a", "b"), ("x", "y"))
    assert r["sequence"][-1] == ("improvement", 1, "y")       # equal counts end on an improvement
    assert r["held"] == ()


@pytest.mark.parametrize("bad", [None, 5, St("a"), b"a"])
def test_note_type(bad):
    refuse("strengths[0]: note of 1 to 60 characters required", (bad,), ())
    refuse("strengths[2]: note of 1 to 60 characters required", ("a", "b", bad), ())
    refuse("improvements[0]: note of 1 to 60 characters required", (), (bad,))
    refuse("improvements[1]: note of 1 to 60 characters required", (), ("a", bad))


@pytest.mark.parametrize("bad", [[], ["a"], None, "x", 5, Tu(("a",))])
def test_shape(bad):
    refuse(SM, bad, ())
    refuse(IM, (), bad)


def test_order():
    refuse(SM, None, None)                                    # strengths shape first
    refuse(IM, ("a",), None)                                  # improvements shape before note checks
    refuse("strengths[1]: note of 1 to 60 characters required", ("a", ""), ("",))
    refuse("strengths[0]: note of 1 to 60 characters required", ("",), (None,))
