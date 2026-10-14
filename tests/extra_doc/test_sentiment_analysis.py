import copy
import random
import re
from fractions import Fraction

import pytest

from sugarcode.extra_doc import sentiment_analysis as m
from sugarcode.extra_doc.sentiment_analysis import SentError, sentiment_analysis as run

F = Fraction
KEYS = "data keys must be exactly text, lexicon, negators"
LEX = [["good", 2], ["great", 3], ["bad", -2], ["awful", -4]]
NEG = ["not", "never"]


def d(text="This is good, not bad. Great!", lex=None, neg=None):
    return {"text": text, "lexicon": [list(e) for e in (LEX if lex is None else lex)],
            "negators": list(NEG if neg is None else neg)}


def bad(data, msg):
    with pytest.raises(SentError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(data):
    """Independent: regex token list, regex fullmatch on the gap, plain arithmetic."""
    lex = {w: wt for w, wt in data["lexicon"]}
    neg = set(data["negators"])
    ms = list(re.finditer(r"[A-Za-z0-9]+", data["text"]))
    rows = []
    for i, mt in enumerate(ms):
        w = mt.group(0).lower()
        if w not in lex:
            continue
        n = False
        if i:
            gap = data["text"][ms[i - 1].end():mt.start()]
            n = ms[i - 1].group(0).lower() in neg and re.fullmatch(r"[ \t]*", gap) is not None
        rows.append((w, lex[w], n, -lex[w] if n else lex[w], mt.start(), mt.end()))
    return ms, rows


def check(data):
    out = run(data)
    ms, rows = oracle(data)
    assert [(x["word"], x["weight"], x["negated"], x["effective"], x["start"], x["end"]) for x in out["matched"]] == rows
    eff = [r[3] for r in rows]
    assert out["score"] == sum(eff)
    assert out["positive_total"] == sum(e for e in eff if e > 0)
    assert out["negative_total"] == sum(e for e in eff if e < 0)
    assert out["label"] == ("positive" if sum(eff) > 0 else "negative" if sum(eff) < 0 else "neutral")
    assert out["token_count"] == len(ms)
    assert F(out["score_per_token"]) == (F(sum(eff), len(ms)) if ms else 0)
    return out


def test_basic():
    out = check(d())
    assert out["score"] == 2 + 2 + 3 and out["label"] == "positive"
    assert out["positive_total"] == 7 and out["negative_total"] == 0
    assert out["token_count"] == 6 and out["score_per_token"] == "7/6"
    assert [x["negated"] for x in out["matched"]] == [False, True, False]
    assert out["status"] == "completed"
    assert out["claims"] == {"human_agreement": False, "absent_is_neutral": False, "weights_validated": False, "real_world": False}
    assert len(out["not_claimed"]) == 4


def test_labels_and_exact_fraction():
    out = check(d("bad awful"))
    assert out["label"] == "negative" and out["score"] == -6 and out["negative_total"] == -6
    assert out["score_per_token"] == "-3"
    out = check(d("good bad"))
    assert out["label"] == "neutral" and out["score"] == 0 and out["score_per_token"] == "0"
    out = check(d("good and then some words here"))
    assert out["score_per_token"] == "1/3" and out["label"] == "positive"
    out = check(d("no sentiment here"))
    assert out["matched"] == [] and out["label"] == "neutral" and out["score"] == 0
    out = check(d("...!!!"))
    assert out["token_count"] == 0 and out["score_per_token"] == "0" and out["label"] == "neutral"


def test_negation_rules():
    cases = [("not good", -2), ("not  \t good", -2), ("not, good", 2), ("not\ngood", 2), ("not not good", -2),
             ("not the good", 2), ("good not", 2), ("never bad", 2), ("NOT GOOD", -2), ("notgood", 0),
             ("not.good", 2), ("not-good", 2), ("not good good", 0), ("not bad bad", 2 - 2)]
    for text, want in cases:
        out = check(d(text))
        assert out["score"] == want, text
    out = check(d("not good"))
    assert out["matched"][0]["negated"] is True and out["matched"][0]["effective"] == -2
    assert out["matched"][0]["weight"] == 2
    out = check(d("not good", neg=[]))
    assert out["score"] == 2 and out["matched"][0]["negated"] is False


def test_totals_split_by_sign():
    out = check(d("good bad not bad awful"))
    assert out["positive_total"] == 2 + 2 and out["negative_total"] == -2 - 4 and out["score"] == -2


def test_tokenization_and_offsets():
    out = check(d("xgood good_ good2 (good) GOOD,good"))
    assert [x["start"] for x in out["matched"]] == [6, 19, 25, 30]
    for c in "aAzZ09":
        lc = c.lower()
        out = check(d(f"{c} {c}x x{c}", [[lc, 1]], []))
        assert [x["start"] for x in out["matched"]] == [0]
    for sep in "`{@[/:":
        out = check(d(f"q{sep}q", [["q", 1]], []))
        assert out["score"] == 2


def test_random_against_oracle():
    rng = random.Random(3)
    words = ["good", "bad", "not", "never", "x", "Great", "awful", "good2"]
    seps = [" ", "  ", "\t", ", ", ".", "\n", "-", ""]
    for _ in range(500):
        text = "".join(rng.choice(words) + rng.choice(seps) for _ in range(rng.randint(1, 14))) or "x"
        check(d(text))


def test_lexicon_and_negator_validation():
    msg = "word must be 1..20 lower-case letters or digits"
    run(d(lex=[["a" * 20, 1]]))
    for w in ["a" * 21, "", "Ab", "a b", "a_", "a-", "\u00e9", "a\n"]:
        bad(d(lex=[[w, 1]]), msg)
        bad(d(neg=[w]), msg)
    run(d(lex=[["az", 1], ["09", 1]]))
    run(d(neg=["az", "09"]))
    run(d(neg=[]))
    for wt in [0, 6, -6, 100]:
        bad(d(lex=[["x", wt]]), "weight must be a nonzero int in -5..5")
    for wt in [-5, -1, 1, 5]:
        run(d(lex=[["x", wt]]))
    bad(d(lex=[["x", 1], ["x", 2]]), "lexicon words must be distinct")
    bad(d(neg=["n", "n"]), "negators must be distinct")
    bad(d(lex=[["not", 1]]), "negators must not be lexicon words")


def test_caps_and_boundaries():
    run(d("a" * 2000))
    bad(d("a" * 2001), "text length out of range")
    bad(d("a" * 10**6), "text length out of range")
    bad(d(""), "text length out of range")
    run(d(lex=[["w%d" % i, 1] for i in range(100)]))
    bad(d(lex=[["w%d" % i, 1] for i in range(101)]), "lexicon must be a list of 1..100 [word, weight] pairs")
    bad(d(lex=[["w", 1]] * 10**5), "lexicon must be a list of 1..100 [word, weight] pairs")
    bad(d(lex=[]), "lexicon must be a list of 1..100 [word, weight] pairs")
    run(d(neg=["n%d" % i for i in range(10)]))
    bad(d(neg=["n%d" % i for i in range(11)]), "negators must be a list of 0..10 words")
    bad(d(neg=["n"] * 10**5), "negators must be a list of 0..10 words")


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint_weight(v):
    bad(d(lex=[["x", v]]), "weight must be an int")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, [], {}, b"a"])
def test_nonstring_slots(v):
    x = d()
    x["text"] = v
    bad(x, "text must be a string")
    bad(d(lex=[[v, 1]]), "lexicon word must be a string")
    bad(d(neg=[v]), "negator must be a string")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainer(v):
    x = d()
    x["lexicon"] = v
    bad(x, "lexicon must be a list of 1..100 [word, weight] pairs")
    x = d()
    x["negators"] = v
    bad(x, "negators must be a list of 0..10 words")
    x = d()
    x["lexicon"] = [v]
    bad(x, "lexicon entry must be a [word, weight] pair")
    for e in (["a"], ["a", 1, 2]):
        x = d()
        x["lexicon"] = [e]
        bad(x, "lexicon entry must be a [word, weight] pair")


def test_ascii_and_control_chars():
    bad(d("caf\u00e9"), "text must be ASCII")
    for c in ["\r", "\x00", "\x1f", "\x7f", "\x0b"]:
        bad(d("a" + c), "text has a disallowed control character")
    for c in ["\n", "\t", " ", "~"]:
        run(d("a" + c))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("text", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("text", "lexicon", "negators"):
        x = d()
        del x[k]
        bad(x, KEYS)
        x["other"] = 1
        bad(x, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["real_world"] = True
    a["matched"][0]["word"] = "zz"
    r = run(x)
    assert r["claims"]["real_world"] is False and r["matched"][0]["word"] == "good"
    assert m.CLAIMS["real_world"] is False
