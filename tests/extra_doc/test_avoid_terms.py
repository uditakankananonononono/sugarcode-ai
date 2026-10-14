import re
import pytest
from sugarcode.extra_doc import avoid_terms as at

S = at.scan
NC = ("what offends any person", "phrases or context", "other scripts or spelling variants",
      "diplomatic quality of the text", "safety of sending the text")
TX = "text: str of 0 to 2000 characters required"
AV = "avoid: tuple of 1 to 20 words required"


class St(str):
    pass


class Tu(tuple):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        S(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def oracle(text, avoid):                  # independent: manual character scan
    words, cur = [], ""
    for ch in text + "\0":
        if ("a" <= ch <= "z") or ("A" <= ch <= "Z"):
            cur += ch
        else:
            if cur:
                words.append(cur.lower())
            cur = ""
    return [(i, w) for i, w in enumerate(words) if w in avoid]


def test_constants():
    assert at.MAX_TEXT == 2000 and at.MAX_AVOID == 20 and at.NOT_CLAIMED == NC


def test_literals():
    assert S("You are Wrong, wrong!", ("wrong",)) == {
        "hits": [(2, "wrong"), (3, "wrong")], "counts": {"wrong": 2},
        "avoid_terms_validated": False, "not_claimed": NC}
    assert S("", ("a",))["hits"] == []
    assert S("a", ("a",))["hits"] == [(0, "a")]
    assert S("xwrong wrongx wrong", ("wrong",))["hits"] == [(2, "wrong")]
    assert S("bad1bad", ("bad",))["hits"] == [(0, "bad"), (1, "bad")]
    assert S("b\u00e9d bad", ("bad",))["hits"] == [(2, "bad")]        # \u00e9 separates: b, d, bad
    assert S("\uff42\uff41\uff44", ("bad",))["hits"] == []
    assert S("bad\nbad", ("bad",))["counts"] == {"bad": 2}
    assert S("dumb bad", ("bad", "dumb"))["counts"] == {"bad": 1, "dumb": 1}
    assert list(S("x", ("zz", "aa"))["counts"]) == ["zz", "aa"]


def test_cyrillic_separates():
    assert S("b\u0430d", ("b",))["hits"] == [(0, "b")]
    assert S("b\u0430d", ("d",))["hits"] == [(1, "d")]
    assert S("b\u0430d", ("bad",))["hits"] == []


def test_oracle():
    import random
    rnd = random.Random(720)
    alpha = "abAB c1\u00e9.\n"
    for _ in range(200):
        t = "".join(rnd.choice(alpha) for _ in range(rnd.randint(0, 25)))
        av = ("a", "b", "ab", "ba")
        r = S(t, av)
        assert r["hits"] == oracle(t, av)


def test_caps():
    assert S("a" * 2000, ("a",))["hits"] == []
    assert S("a " * 1000, ("a",))["counts"] == {"a": 1000}
    refuse(TX, "a" * 2001, ("a",))
    w = tuple(chr(97 + i) for i in range(20))
    assert len(S("", w)["counts"]) == 20
    refuse(AV, "", w + ("z" * 2,))
    assert S("a" * 20, ("a" * 20,))["hits"] == [(0, "a" * 20)]
    assert S("a" * 21, ("a" * 20,))["hits"] == []


@pytest.mark.parametrize("bad", [None, 5, b"a", ["a"], St("a"), ("a",)])
def test_text_type(bad):
    refuse(TX, bad, ("a",))


@pytest.mark.parametrize("bad", [(), ["a"], None, "a", Tu(("a",)), tuple("abcdefghijklmnopqrstu")])
def test_avoid_shape(bad):
    refuse(AV, "x", bad)


@pytest.mark.parametrize("bad", [None, 1, "", "A", "a1", "a b", "a\n", "\u00e9", "a\u00e9", "\uff41", "\u0430", "a" * 21, St("a"), b"a"])
def test_avoid_item(bad):
    refuse("avoid[0]: word of 1 to 20 lowercase a-z letters required", "x", (bad,))
    refuse("avoid[1]: word of 1 to 20 lowercase a-z letters required", "x", ("a", bad))


def test_distinct_and_order():
    refuse("avoid: words must be distinct", "x", ("a", "b", "a"))
    refuse(TX, 5, ())
    refuse(AV, "x", (None,) * 21)
    refuse("avoid[0]: word of 1 to 20 lowercase a-z letters required", "x", (None, None))
    refuse("avoid[1]: word of 1 to 20 lowercase a-z letters required", "x", ("a", "A", "a"))
