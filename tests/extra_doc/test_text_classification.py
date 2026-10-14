import copy
import random
import re
from collections import Counter
from fractions import Fraction

import pytest

from sugarcode.extra_doc import text_classification as m
from sugarcode.extra_doc.text_classification import ClsError, text_classification as run

F = Fraction
KEYS = "data keys must be exactly examples, text"
EX = [["spam", "buy cheap pills now"], ["spam", "cheap pills cheap"], ["ham", "meeting at noon"], ["ham", "lunch meeting now"]]


def d(text="cheap meeting", ex=None):
    return {"examples": [list(e) for e in (EX if ex is None else ex)], "text": text}


def bad(data, msg):
    with pytest.raises(ClsError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(data):
    """Independent: Counter-based, regex tokens, scores via the closed form with exponents."""
    toks = lambda s: re.findall(r"[a-z0-9]+", s.lower())
    labels = sorted({l for l, _ in data["examples"]})
    n = len(data["examples"])
    cnt = {l: Counter() for l in labels}
    nd = Counter(l for l, _ in data["examples"])
    for l, t in data["examples"]:
        cnt[l].update(toks(t))
    vocab = set().union(*[set(c) for c in cnt.values()])
    V = len(vocab)
    q = Counter(w for w in toks(data["text"]) if w in vocab)
    sc = {}
    for l in labels:
        T = sum(cnt[l].values())
        s = F(nd[l], n)
        for w, k in q.items():
            s *= F(cnt[l][w] + 1, T + V) ** k
        sc[l] = s
    z = sum(sc.values())
    post = {l: sc[l] / z for l in labels}
    best = max(post.values())
    win = [l for l in labels if post[l] == best]
    nq = len(toks(data["text"]))
    return post, win, V, sum(q.values()), nq - sum(q.values())


def check(data):
    out = run(data)
    post, win, V, used, ign = oracle(data)
    assert {k: F(v) for k, v in out["posterior"].items()} == post and list(out["posterior"]) == sorted(post)
    assert sum(F(v) for v in out["posterior"].values()) == 1
    assert out["predicted"] == win[0] and out["tie"] is (len(win) > 1)
    assert out["vocabulary_size"] == V and out["tokens_used"] == used and out["tokens_ignored"] == ign
    return out


def test_hand_worked_example():
    # vocab: buy cheap pills now meeting at noon lunch = 8 ; spam tokens 7, ham tokens 6
    out = run(d("cheap"))
    ps = F(1, 2) * F(3 + 1, 7 + 8)           # cheap occurs 3x in spam
    ph = F(1, 2) * F(0 + 1, 6 + 8)
    assert F(out["posterior"]["spam"]) == ps / (ps + ph)
    assert F(out["posterior"]["ham"]) == ph / (ps + ph)
    assert out["vocabulary_size"] == 8 and out["predicted"] == "spam"
    assert out["status"] == "completed"
    assert out["claims"] == {"correct": False, "representative": False, "independence": False, "real_world": False}
    assert len(out["not_claimed"]) == 4


def test_basic_and_ignored_tokens():
    out = check(d())
    assert out["tokens_used"] == 2 and out["tokens_ignored"] == 0
    out = check(d("cheap unknownword meeting zzz"))
    assert out["tokens_used"] == 2 and out["tokens_ignored"] == 2
    out = check(d("only unknown words"))
    assert out["posterior"] == {"ham": "1/2", "spam": "1/2"} and out["tie"] is True and out["predicted"] == "ham"


def test_priors_and_repeats_counted():
    ex = [["a", "x"], ["a", "x"], ["a", "x"], ["b", "y"]]
    out = check(d("zzz", ex))
    assert out["posterior"] == {"a": "3/4", "b": "1/4"}
    out = check(d("x x x x", ex))
    assert F(out["posterior"]["a"]) > F(out["posterior"]["b"])
    out1, out2 = run(d("x", ex)), run(d("x x", ex))
    assert out1["posterior"] != out2["posterior"]


def test_tie_goes_to_alphabetically_first_label():
    ex = [["zebra", "p"], ["apple", "q"]]
    out = check(d("r", ex))
    assert out["tie"] is True and out["predicted"] == "apple"
    out = check(d("p", ex))
    assert out["predicted"] == "zebra" and out["tie"] is False
    assert list(out["posterior"]) == ["apple", "zebra"]


def test_tokenization_boundaries():
    for c in "aAzZ09":
        lc = c.lower()
        ex = [["a", f"q{lc}"], ["b", "other"]]
        out = check(d(f"Q{c}", ex))
        assert out["tokens_used"] == 1 and out["predicted"] == "a"
    for sep in "`{@[/:":
        out = check(d(f"q{sep}q", [["a", "q"], ["b", "r"]]))
        assert out["tokens_used"] == 2


def test_random_against_oracle():
    rng = random.Random(21)
    words = ["red", "blue", "sun", "x1", "Red", "moon", "z9", "a"]
    for _ in range(300):
        ex = [[rng.choice(["p", "q", "r"]), " ".join(rng.choice(words) for _ in range(rng.randint(1, 6)))]
              for _ in range(rng.randint(2, 8))]
        if len({e[0] for e in ex}) < 2:
            continue
        check(d(" ".join(rng.choice(words + ["new"]) for _ in range(rng.randint(1, 6))), ex))


def test_label_and_example_validation():
    run(d(ex=[["a" * 10, "x"], ["b", "y"]]))
    for lab in ["a" * 11, "", "Ab", "a1", "a_", "a b", "\u00e9"]:
        bad(d(ex=[[lab, "x"], ["b", "y"]]), "label must be 1..10 lower-case ASCII letters")
    bad(d(ex=[["a", "x"], ["a", "y"]]), "examples must contain at least two distinct labels")
    bad(d(ex=[["a", "!!!"], ["b", "???"]]), "example texts have no tokens")
    run(d(ex=[["a", "!!!"], ["b", "y"]]))


def test_caps_and_boundaries():
    run(d("x", [["a", "x" * 200], ["b", "y"]]))
    bad(d("x", [["a", "x" * 201], ["b", "y"]]), "example text length out of range")
    bad(d("x", [["a", "x" * 10**6], ["b", "y"]]), "example text length out of range")
    bad(d("x", [["a", ""], ["b", "y"]]), "example text length out of range")
    bad(d("x" * 201), "text length out of range")
    bad(d("x" * 10**6), "text length out of range")
    bad(d(""), "text length out of range")
    run(d(ex=[["a", "x"], ["b", "y"]] * 20))
    bad(d(ex=[["a", "x"], ["b", "y"]] * 21), "examples must be a list of 2..40 [label, text] pairs")
    bad(d(ex=[["a", "x"]] * 10**5), "examples must be a list of 2..40 [label, text] pairs")
    bad(d(ex=[["a", "x"]]), "examples must be a list of 2..40 [label, text] pairs")
    bad(d(ex=[]), "examples must be a list of 2..40 [label, text] pairs")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, [], {}, b"a"])
def test_nonstring_slots(v):
    bad(d(v), "text must be a string")
    bad(d(ex=[["a", v], ["b", "y"]]), "example text must be a string")
    bad(d(ex=[[v, "x"], ["b", "y"]]), "label must be a string")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a", "b")])
def test_noncontainer(v):
    x = d()
    x["examples"] = v
    bad(x, "examples must be a list of 2..40 [label, text] pairs")
    x = d()
    x["examples"] = [v, ["b", "y"]]
    bad(x, "example must be a [label, text] pair")
    for e in (["a"], ["a", "b", "c"]):
        x = d()
        x["examples"] = [e, ["b", "y"]]
        bad(x, "example must be a [label, text] pair")


def test_ascii_only():
    bad(d("caf\u00e9"), "text must be ASCII")
    bad(d(ex=[["a", "caf\u00e9"], ["b", "y"]]), "example text must be ASCII")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("text", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("examples", "text"):
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
    a["claims"]["correct"] = True
    a["posterior"]["spam"] = "0"
    r = run(x)
    assert r["claims"]["correct"] is False and r["posterior"]["spam"] != "0"
    assert m.CLAIMS["correct"] is False


def test_exactly_forty_examples_accepted_forty_one_refused():
    base = [["a", "x"], ["b", "y"]] * 20
    assert len(base) == 40
    run(d(ex=base))
    bad(d(ex=base + [["a", "x"]]), "examples must be a list of 2..40 [label, text] pairs")


@pytest.mark.parametrize("c", list("aAzZ09"))
def test_boundary_char_is_part_of_the_token(c):
    lc = c.lower()
    out = run(d("q", [["a", f"q{c}"], ["b", "other"]]))
    assert out["tokens_used"] == 0 and out["tokens_ignored"] == 1
    out = run(d("q", [["a", f"{c}q"], ["b", "other"]]))
    assert out["tokens_used"] == 0
    out = run(d(f"{c}", [["a", f"{lc}"], ["b", "other"]]))
    assert out["tokens_used"] == 1 and out["predicted"] == "a"
