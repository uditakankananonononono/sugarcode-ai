from fractions import Fraction as Fr
import random
import pytest
from sugarcode.extra_doc import transcreation as t

C = t.check


def test_constants():
    assert (t.MAX_TEXT, t.MAX_ITEMS, t.MAX_ITEM_LEN, t.NEAR_LITERAL) == (5000, 50, 100, Fr(3, 4))
    assert t.STATUS_NOTE.startswith("PARTIAL") and "lexical-overlap proxy" in t.STATUS_NOTE


def test_overlap_hand_values_and_threshold():
    assert C("Just do it", "Just do it")["overlap"] == 1 and C("Just do it", "Just do it")["verdict"] == "near_literal"
    assert C("buy now save big", "save big buy now")["overlap"] == 1
    r = C("a b c d", "c d e f")
    assert r["overlap"] == Fr(1, 3) and r["verdict"] == "recreated"
    r = C("a b c d", "a b c")
    assert r["overlap"] == Fr(3, 4) and r["verdict"] == "near_literal"     # exactly the threshold
    r = C("a b c d", "a b c e")
    assert r["overlap"] == Fr(3, 5) and r["verdict"] == "recreated"
    r = C("a b c", "a b")
    assert r["overlap"] == Fr(2, 3) and r["verdict"] == "recreated"
    assert C("a b c d", "a b c d e")["overlap"] == Fr(4, 5)
    assert C("one two", "three four")["overlap"] == 0
    assert C("!!!", "???")["overlap"] == 0 and C("!!!", "???")["verdict"] == "recreated"


def test_words_are_unicode_lowercased_and_deduplicated():
    assert C("café au lait", "CAFÉ noir")["overlap"] == Fr(1, 4)
    assert C("go go go", "go")["overlap"] == 1
    assert C("snake_case 42", "SNAKE_CASE 42 x")["overlap"] == Fr(2, 3)
    assert C("hello, world!", "world hello")["overlap"] == 1


def test_protected_words_removed_from_overlap_and_checked_verbatim():
    r = C("Nike just do it", "Nike fais-le", protected=["Nike"])
    assert r["overlap"] == 0 and r["missing_protected"] == [] and r["ok"] is True
    r = C("Nike just do it", "nike fais-le", protected=["Nike"])
    assert r["missing_protected"] == ["Nike"] and r["ok"] is False
    r = C("Nike just do it", "Nike just do it")
    assert r["overlap"] == 1
    r = C("Air Max shoes", "Air Max chaussures", protected=["Air Max"])
    assert r["overlap"] == 0 and r["missing_protected"] == []
    r = C("Air Max shoes", "chaussures", protected=("Air Max", "shoes"))
    assert r["missing_protected"] == ["Air Max", "shoes"]


def test_required_and_forbidden_case_insensitive():
    r = C("src", "Great Deal today", required=["great deal", "TODAY"], forbidden=["cheap"])
    assert r["missing_required"] == [] and r["forbidden_found"] == [] and r["ok"] is True
    r = C("src", "Great Deal", required=["great deal", "today"], forbidden=["GREAT"])
    assert r["missing_required"] == ["today"] and r["forbidden_found"] == ["GREAT"] and r["ok"] is False
    r = C("src", "cheapest", forbidden=["cheap", "pricey"])
    assert r["forbidden_found"] == ["cheap"]


def test_length_ratio_and_cap_boundary():
    r = C("abcd", "abcdef")
    assert r["length_ratio"] == Fr(3, 2) and r["too_long"] is False and r["ok"] is True
    assert C("abcd", "abcdef", max_chars=6)["too_long"] is False
    r = C("abcd", "abcdef", max_chars=5)
    assert r["too_long"] is True and r["ok"] is False
    assert C("x", "y", max_chars=1)["too_long"] is False
    assert C("x", "yy", max_chars=1)["too_long"] is True
    assert C("abc", "a", max_chars=5000)["length_ratio"] == Fr(1, 3)
    assert C("abc", "abcdef")["status"] == t.STATUS_NOTE


def test_overlap_against_split_oracle():
    rnd = random.Random(14)
    vocab = ["red", "blue", "sun", "moon", "tea", "sky", "ink", "oak"]
    for _ in range(200):
        a = [rnd.choice(vocab) for _ in range(rnd.randint(1, 7))]
        b = [rnd.choice(vocab) for _ in range(rnd.randint(1, 7))]
        drop = set(rnd.sample(vocab, rnd.randint(0, 2)))
        sa, sb = set(a) - drop, set(b) - drop
        want = Fr(len(sa & sb), len(sa | sb)) if sa | sb else Fr(0)
        r = C(" ".join(a), " ".join(b), protected=sorted(drop))
        assert r["overlap"] == want
        assert r["verdict"] == ("near_literal" if want >= Fr(3, 4) else "recreated")


@pytest.mark.parametrize("kw", [
    dict(source=5, candidate="a"), dict(source="a", candidate=None), dict(source="", candidate="a"),
    dict(source="a", candidate="  "), dict(source="a" * 5001, candidate="a"), dict(source="a", candidate="a" * 5001),
    dict(source="a", candidate="a", protected="Nike"), dict(source="a", candidate="a", required=5),
    dict(source="a", candidate="a", forbidden=None), dict(source="a", candidate="a", protected=[""]),
    dict(source="a", candidate="a", protected=[" "]), dict(source="a", candidate="a", protected=[5]),
    dict(source="a", candidate="a", required=["x" * 101]), dict(source="a", candidate="a", forbidden=["x"] * 51),
    dict(source="a", candidate="a", max_chars=0), dict(source="a", candidate="a", max_chars=5001),
    dict(source="a", candidate="a", max_chars=True), dict(source="a", candidate="a", max_chars=1.5),
    dict(source="a", candidate="a", max_chars="5"), dict(source="a", candidate="a", max_chars=-1),
])
def test_rejects(kw):
    with pytest.raises(ValueError):
        C(**kw)


def test_limits_and_messages():
    assert C("a" * 5000, "b" * 5000)["length_ratio"] == 1
    assert C("a", "a", protected=["x" * 100] * 50)["missing_protected"] == ["x" * 100] * 50
    assert C("a", "a", max_chars=1)["too_long"] is False and C("a", "a", max_chars=5000)["too_long"] is False
    for kw, msg in [(dict(source=5, candidate="a"), "source: text required"),
                    (dict(source="a", candidate=5), "candidate: text required"),
                    (dict(source=" ", candidate="a"), "source: must not be empty"),
                    (dict(source="a", candidate=" "), "candidate: must not be empty"),
                    (dict(source="a" * 5001, candidate="a"), "source: longer than 5000 characters"),
                    (dict(source="a", candidate="a" * 5001), "candidate: longer than 5000 characters"),
                    (dict(source="a", candidate="a", protected="x"), "protected: list required"),
                    (dict(source="a", candidate="a", required=3), "required: list required"),
                    (dict(source="a", candidate="a", forbidden=3), "forbidden: list required"),
                    (dict(source="a", candidate="a", protected=["x"] * 51), "protected: more than 50 items"),
                    (dict(source="a", candidate="a", required=[""]), "required: non-empty strings required"),
                    (dict(source="a", candidate="a", forbidden=["x" * 101]), "forbidden: item longer than 100 characters"),
                    (dict(source="a", candidate="a", max_chars=1.5), "max_chars: whole number required"),
                    (dict(source="a", candidate="a", max_chars=True), "max_chars: whole number required"),
                    (dict(source="a", candidate="a", max_chars=0), r"max_chars: must be within \[1, 5000\]"),
                    (dict(source="a", candidate="a", max_chars=5001), r"max_chars: must be within \[1, 5000\]")]:
        with pytest.raises(ValueError, match=msg):
            C(**kw)


def test_ok_false_for_each_single_cause():
    base = C("src", "Great Deal", required=["great deal"], forbidden=["cheap"])
    assert base["ok"] is True
    r = C("src", "Great Deal", required=["missing phrase"])
    assert r["missing_required"] == ["missing phrase"] and r["missing_protected"] == [] and r["forbidden_found"] == []
    assert r["too_long"] is False and r["ok"] is False
    r = C("src", "Great Deal", forbidden=["deal"])
    assert r["forbidden_found"] == ["deal"] and r["missing_protected"] == [] and r["missing_required"] == []
    assert r["too_long"] is False and r["ok"] is False
    r = C("src", "Great Deal", protected=["Nope"])
    assert r["missing_protected"] == ["Nope"] and r["missing_required"] == [] and r["forbidden_found"] == [] and r["ok"] is False
    r = C("src", "Great Deal", max_chars=3)
    assert r["too_long"] is True and r["missing_protected"] == [] and r["missing_required"] == [] and r["ok"] is False


def test_documented_quirks():
    r = C("Buy now", "Buy now", ["Buy now"])
    assert r["overlap"] == 0 and r["verdict"] == "recreated" and r["missing_protected"] == [] and r["ok"] is True
    assert C("Buy now", "Buy now")["overlap"] == 1
    assert C("don't stop", "don t stop")["overlap"] == 1
    assert C("don't stop", "dont stop")["overlap"] == Fr(1, 4)
    r = C("src", "nike", protected=["Nike"], required=["NIKE"])          # protected is case-sensitive, required is not
    assert r["missing_protected"] == ["Nike"] and r["missing_required"] == []
    assert "Quirks" in t.__doc__ and "don" in t.__doc__ and 'check("Buy now", "Buy now", ["Buy now"])' in t.__doc__
