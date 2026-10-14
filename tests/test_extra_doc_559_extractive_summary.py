import inspect
import random
import re
from collections import Counter

import pytest
from sugarcode.extra_doc import extractive_summary as es

S = es.summarize


def pick(r):
    return [(x["index"], x["score"], x["text"]) for x in r["sentences"]]


def test_constants_signature():
    assert (es.MAX_TEXT, es.MAX_COUNT) == (5000, 10)
    assert es.STATUS_NOTE.startswith("PARTIAL") and "no rewriting" in es.STATUS_NOTE
    sig = inspect.signature(S)
    assert list(sig.parameters) == ["text", "count"] and sig.parameters["count"].default == 1


def test_hand_literals():
    t = "Cats chase mice. Dogs chase cats. Mice hide."
    # freq: cats2 chase2 mice2 dogs1 hide1 ; scores: s0 cats+chase+mice=6, s1 dogs+chase+cats=1+2+2=5, s2 mice+hide=3
    r = S(t, 2)
    assert pick(r) == [(0, 6, "Cats chase mice."), (1, 5, "Dogs chase cats.")]
    assert r["total_sentences"] == 3 and r["status_note"] == es.STATUS_NOTE
    assert pick(S(t)) == [(0, 6, "Cats chase mice.")]                       # default count 1
    assert pick(S(t, 3)) == [(0, 6, "Cats chase mice."), (1, 5, "Dogs chase cats."), (2, 3, "Mice hide.")]
    assert pick(S(t, 10)) == pick(S(t, 3))                                  # count above the sentence total
    # repeated word within one sentence counts once: "go go go." score = freq(go)=3 only
    assert pick(S("go go go. stop now.", 2)) == [(0, 3, "go go go."), (1, 2, "stop now.")]
    # tie goes to the earlier sentence, output in original order
    assert pick(S("aa bb. cc dd. ee ff.", 2)) == [(0, 2, "aa bb."), (1, 2, "cc dd.")]
    assert pick(S("x y. big big big. z w.", 1)) == [(1, 3, "big big big.")]
    assert pick(S("no marks here", 1)) == [(0, 3, "no marks here")]
    assert pick(S("one. ... two!  ?? three", 3)) == [(0, 1, "one."), (1, 1, "two!"), (2, 1, "three")]
    assert S("... !!!", 1) == {"sentences": [], "total_sentences": 0, "status_note": es.STATUS_NOTE}
    assert pick(S("  lead and trail.  \n", 1)) == [(0, 3, "lead and trail.")]


def test_selected_shown_in_original_order_not_score_order():
    t = "a. b b. c c c."
    # scores a=1, bb=2, ccc=3 ; count 2 picks sentences 1 and 2 (shown in text order)
    assert [x["index"] for x in S(t, 2)["sentences"]] == [1, 2]
    assert [x["index"] for x in S(t, 1)["sentences"]] == [2]


def test_oracle_regex_counter():
    rnd = random.Random(559)
    for _ in range(300):
        parts = []
        for _ in range(rnd.randint(1, 6)):
            parts.append(" ".join(rnd.choice(["a", "b", "c", "d", "E"]) for _ in range(rnd.randint(0, 4))) + rnd.choice([".", "!", "?", ""]))
        text = " ".join(parts) or "x"
        k = rnd.randint(1, 4)
        segs = [m.group(0).strip() for m in re.finditer(r"[^.!?]*[.!?]|[^.!?]+$", text)]
        segs = [s for s in segs if re.search(r"[A-Za-z0-9]", s)]
        toks = [[t.lower() for t in re.findall(r"[A-Za-z0-9]+", s)] for s in segs]
        freq = Counter(t for ts in toks for t in ts)
        sc = [sum(freq[t] for t in set(ts)) for ts in toks]
        order = sorted(range(len(segs)), key=lambda i: (-sc[i], i))[:k]
        want = [(i, sc[i], segs[i]) for i in sorted(order)]
        assert pick(S(text, k)) == want, (text, k)


def test_caps_both_sides():
    assert S("a" * 5000)["total_sentences"] == 1
    with pytest.raises(ValueError, match=r"^text: 1 to 5000 characters required$"):
        S("a" * 5001)
    with pytest.raises(ValueError, match=r"^text: 1 to 5000 characters required$"):
        S("")
    assert S("a.", 1)["total_sentences"] == 1 and S("a.", 10)["total_sentences"] == 1
    with pytest.raises(ValueError, match=r"^count: must be within 1 to 10$"):
        S("a.", 0)
    with pytest.raises(ValueError, match=r"^count: must be within 1 to 10$"):
        S("a.", 11)


def test_type_refusals_and_order():
    for bad in (None, 5, b"abc", ["a."], 1.5):
        with pytest.raises(ValueError, match=r"^text: string required$"):
            S(bad)
    for bad in (True, False, 1.0, "1", None):
        with pytest.raises(ValueError, match=r"^count: integer required$"):
            S("a.", bad)
    with pytest.raises(ValueError, match=r"^count: integer required$"):
        S(5, True)
    with pytest.raises(ValueError, match=r"^count: must be within 1 to 10$"):
        S(5, 99)
    for ch in "@[`{/:":
        assert S(f"x{ch}y.")["sentences"][0]["score"] == 2, ch
    for ch in "aAzZ09":
        assert S(f"x{ch}y.")["sentences"][0]["score"] == 1, ch


def test_marks_adjacent_to_next_sentence():
    assert pick(S("ab.cd!ef?gh", 4)) == [(0, 1, "ab."), (1, 1, "cd!"), (2, 1, "ef?"), (3, 1, "gh")]
    assert pick(S("a.b", 2)) == [(0, 1, "a."), (1, 1, "b")]
    assert pick(S(".a.", 1)) == [(0, 1, "a.")]
