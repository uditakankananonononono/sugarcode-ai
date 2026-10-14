import copy
import random
import re

import pytest

from sugarcode.extra_doc import relation_extraction as m
from sugarcode.extra_doc.relation_extraction import ReError, relation_extraction as run

KEYS = "data keys must be exactly text, entities, relations"
ENT = [["person", "Ada"], ["person", "Bob Stone"], ["org", "ACME"], ["org", "ACME Labs"]]
REL = [["works_at", "works at"], ["founded", "founded"], ["met", "met with"]]


def d(text="Ada works at ACME Labs. Bob Stone founded ACME.", ents=None, rels=None):
    return {"text": text, "entities": [list(e) for e in (ENT if ents is None else ents)],
            "relations": [list(r) for r in (REL if rels is None else rels)]}


def bad(data, msg):
    with pytest.raises(ReError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(data):
    """Independent: regex sentence split, regex mention scan, regex fullmatch on the gap."""
    ents = []
    for label, ph in data["entities"]:
        toks = re.findall(r"[A-Za-z0-9]+", ph.lower())
        ents.append((len(toks), label, toks))
    ents.sort(key=lambda e: -e[0])
    alts = ["(?P<g%d>%s)" % (i, r"[ \t]+".join(re.escape(t) for t in e[2])) for i, e in enumerate(ents)]
    ement = re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(alts) + r")(?![A-Za-z0-9])", re.I)
    relpats = []
    for name, ph in data["relations"]:
        toks = re.findall(r"[A-Za-z0-9]+", ph.lower())
        relpats.append((name, re.compile(r"[ \t]*" + r"[ \t]+".join(re.escape(t) for t in toks) + r"[ \t]*", re.I)))
    triples, found, scanned = [], 0, 0
    segs, start = [], 0
    for mt in re.finditer(r"[.!?\n]", data["text"]):
        segs.append((start, mt.start()))
        start = mt.end()
    segs.append((start, len(data["text"])))
    for a, b in segs:
        sub = data["text"][a:b]
        if re.search(r"[A-Za-z0-9]", sub):
            scanned += 1
        ms = []
        for mt in ement.finditer(sub):
            n, label, toks = ents[int(mt.lastgroup[1:])]
            ms.append({"label": label, "phrase": " ".join(toks), "start": mt.start() + a, "end": mt.end() + a})
        found += len(ms)
        for x, y in zip(ms, ms[1:]):
            gap = data["text"][x["end"]:y["start"]]
            for name, rp in relpats:
                if rp.fullmatch(gap):
                    triples.append({"subject": x, "relation": name, "object": y})
    return triples, found, scanned


def check(data):
    out = run(data)
    t, f, s = oracle(data)
    assert out["triples"] == t
    assert out["mentions_found"] == f and out["sentences_scanned"] == s
    return out


def test_basic():
    out = check(d())
    tx = d()["text"]
    assert [(x["subject"]["phrase"], x["relation"], x["object"]["phrase"]) for x in out["triples"]] == [
        ("ada", "works_at", "acme labs"), ("bob stone", "founded", "acme")]
    assert out["triples"][0]["subject"] == {"label": "person", "phrase": "ada", "start": 0, "end": 3}
    assert out["triples"][1]["object"]["start"] == tx.index("ACME.")
    assert out["mentions_found"] == 4 and out["sentences_scanned"] == 2
    assert out["status"] == "completed"
    assert out["claims"] == {"truth": False, "negation_handled": False, "completeness": False, "real_world": False}
    assert len(out["not_claimed"]) == 4


def test_gap_must_be_exactly_a_relation():
    cases = [
        ("Ada works at ACME", 1), ("Ada   works \t at  ACME", 1), ("Ada WORKS AT acme", 1),
        ("Ada works ACME", 0), ("Ada works at at ACME", 0), ("Ada, works at ACME", 0),
        ("Ada works at, ACME", 0), ("Ada works at the ACME", 0), ("Ada ACME", 0),
        ("Ada founded ACME", 1), ("Ada foundedx ACME", 0), ("Ada works-at ACME", 0),
        ("Ada met with ACME", 1), ("Ada with met ACME", 0), ("Ada (works at) ACME", 0),
        ("Ada works at ACME", 1),
    ]
    for text, n in cases:
        out = check(d(text))
        assert len(out["triples"]) == n, text


def test_sentence_boundaries_block_relations():
    for t in ["Ada.works at ACME", "Ada works at.ACME", "Ada works!at ACME", "Ada?works at ACME",
              "Ada\nworks at ACME", "Ada works\nat ACME", "Ada works at\nACME"]:
        assert check(d(t))["triples"] == [], t
    out = check(d("Ada works at ACME\nBob Stone founded ACME"))
    assert len(out["triples"]) == 2 and out["sentences_scanned"] == 2


def test_chain_and_consecutive_only():
    out = check(d("Ada met with Bob Stone founded ACME"))
    assert [(x["subject"]["phrase"], x["relation"], x["object"]["phrase"]) for x in out["triples"]] == [
        ("ada", "met", "bob stone"), ("bob stone", "founded", "acme")]
    # a non-consecutive pair is not linked even when the middle is another entity
    out = check(d("Ada works at Bob Stone ACME"))
    assert [(x["subject"]["phrase"], x["object"]["phrase"]) for x in out["triples"]] == [("ada", "bob stone")]
    out = check(d("Ada ACME founded ACME Labs"))
    assert [(x["subject"]["phrase"], x["object"]["phrase"]) for x in out["triples"]] == [("acme", "acme labs")]


def test_longest_entity_wins():
    out = check(d("Ada founded ACME Labs"))
    assert out["triples"][0]["object"]["phrase"] == "acme labs"
    out = check(d("Ada founded ACME Lab"))
    assert out["triples"][0]["object"]["phrase"] == "acme"
    assert out["mentions_found"] == 2


def test_relation_not_inferred_symmetric_or_inverse():
    out = check(d("ACME works at Ada"))
    assert len(out["triples"]) == 1 and out["triples"][0]["subject"]["phrase"] == "acme"
    assert out["triples"][0]["object"]["phrase"] == "ada"


def test_negation_still_matches_documented():
    out = check(d("Ada works at ACME"))
    assert len(out["triples"]) == 1
    assert len(check(d("Ada never works at ACME"))["triples"]) == 0


def test_counters():
    out = check(d("Hello. ... !! 123\n   \nAda"))
    assert out["sentences_scanned"] == 3 and out["mentions_found"] == 1
    out = check(d("....."))
    assert out["sentences_scanned"] == 0 and out["triples"] == []


def test_random_against_oracle():
    rng = random.Random(9)
    words = ["Ada", "Bob", "Stone", "ACME", "works", "at", "met", "with", "x"]
    seps = [" ", "  ", "\t", ", ", ".", "\n", " ! ", ""]
    for _ in range(500):
        text = ""
        for _ in range(rng.randint(1, 16)):
            text += rng.choice(words) + rng.choice(seps)
        text = text or "x"
        ents = [["p", "Ada"], ["q", "Bob Stone"], ["q", "Bob"], ["r", "ACME"]]
        rels = [["w", "works at"], ["m", "met with"], ["a", "at"]]
        rng.shuffle(ents)
        rng.shuffle(rels)
        check(d(text, ents, rels))


def test_entity_and_relation_validation():
    run(d(ents=[["a", "x y z w v u"]]))
    bad(d(ents=[["a", "x y z w v u t"]]), "entities phrase must have 1..6 tokens")
    bad(d(rels=[["a", "x y z w v"]]), "relations phrase must have 1..4 tokens")
    run(d(rels=[["a", "x y z w"]]))
    bad(d(ents=[["a", "  "]]), "entities phrase must have 1..6 tokens")
    bad(d(ents=[["a", ""]]), "entities phrase length out of range")
    run(d(ents=[["a", "x" * 40]]))
    bad(d(ents=[["a", "x" * 41]]), "entities phrase length out of range")
    bad(d(rels=[["a", "x" * 41]]), "relations phrase length out of range")
    for c in ["-", ".", ",", "\n", "_", "!"]:
        bad(d(ents=[["a", "x" + c + "y"]]), "entities phrase may contain only letters, digits, spaces and tabs")
        bad(d(rels=[["a", "x" + c + "y"]]), "relations phrase may contain only letters, digits, spaces and tabs")
    bad(d(ents=[["a", "New York"], ["b", "new  YORK"]]), "entities phrases must be distinct")
    bad(d(rels=[["a", "x"], ["b", "X"]]), "relations phrases must be distinct")
    run(d(ents=[["a", "x"]], rels=[["a", "x"]]))      # the same phrase may be both
    msg = "entity label must be 1..10 lower-case ASCII letters"
    run(d(ents=[["a" * 10, "x"]]))
    for lab in ["a" * 11, "", "Ab", "a1", "a_", "a b", "\u00e9"]:
        bad(d(ents=[[lab, "x"]]), msg)
    msg = "relation name must be 1..20 lower-case letters or underscores"
    run(d(rels=[["a_" * 10, "x"]]))
    run(d(rels=[["_", "x"]]))
    for nm in ["a" * 21, "", "Ab", "a1", "a-b", "a b", "\u00e9"]:
        bad(d(rels=[[nm, "x"]]), msg)


def test_caps_and_boundaries():
    run(d("a" * 2000))
    bad(d("a" * 2001), "text length out of range")
    bad(d("a" * 10**6), "text length out of range")
    bad(d(""), "text length out of range")
    run(d(ents=[["a", "w%d" % i] for i in range(50)]))
    bad(d(ents=[["a", "w%d" % i] for i in range(51)]), "entities must be a list of 1..50 pairs")
    bad(d(ents=[["a", "w"]] * 10**5), "entities must be a list of 1..50 pairs")
    bad(d(ents=[]), "entities must be a list of 1..50 pairs")
    run(d(rels=[["a", "w%d" % i] for i in range(20)]))
    bad(d(rels=[["a", "w%d" % i] for i in range(21)]), "relations must be a list of 1..20 pairs")
    bad(d(rels=[["a", "w"]] * 10**5), "relations must be a list of 1..20 pairs")
    bad(d(rels=[]), "relations must be a list of 1..20 pairs")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, [], {}, b"a"])
def test_nonstring_slots(v):
    x = d()
    x["text"] = v
    bad(x, "text must be a string")
    for key in ("entities", "relations"):
        for pair in ([v, "x"], ["a", v]):
            x = d()
            x[key] = [pair]
            bad(x, f"{key} name and phrase must be strings")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a", "b")])
def test_nonlist_containers(v):
    for key, hi in (("entities", 50), ("relations", 20)):
        x = d()
        x[key] = v
        bad(x, f"{key} must be a list of 1..{hi} pairs")
        x = d()
        x[key] = [v]
        bad(x, f"{key} entry must be a pair")
        for e in (["a"], ["a", "b", "c"]):
            x = d()
            x[key] = [e]
            bad(x, f"{key} entry must be a pair")


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
    x = d()
    x["extra"] = 1
    bad(x, KEYS)
    for k in ("text", "entities", "relations"):
        x = d()
        del x[k]
        bad(x, KEYS)
        x["other"] = 1
        bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims_independent_dicts():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["truth"] = True
    assert run(x)["claims"]["truth"] is False and m.CLAIMS["truth"] is False
    out = run(d("Ada works at ACME. Ada founded ACME."))
    out["triples"][0]["subject"]["label"] = "zz"
    assert out["triples"][1]["subject"]["label"] == "person"


def test_multi_token_entity_gaps_each_position():
    ents = [["e", "a b c d"], ["f", "x"]]
    rels = [["r", "rel"]]
    good = "a b c d rel x"
    assert len(check(d(good, ents, rels))["triples"]) == 1
    for bad_text in ["a, b c d rel x", "a b, c d rel x", "a b c, d rel x", "a-b c d rel x", "a b c\nd rel x",
                     "a b c d, rel x"]:
        out = check(d(bad_text, ents, rels))
        assert out["triples"] == [], bad_text
    out = check(d("a \t b  c\t d  rel \t x", ents, rels))
    assert len(out["triples"]) == 1 and out["triples"][0]["subject"]["phrase"] == "a b c d"
    # 3-token entity, bad gap only at the first or only at the last position
    ents = [["e", "p q r"], ["f", "x"]]
    for t in ["p, q r rel x", "p q, r rel x"]:
        assert check(d(t, ents, rels))["triples"] == [], t
    assert len(check(d("p q r rel x", ents, rels))["triples"]) == 1


@pytest.mark.parametrize("c", list("aAzZ09"))
def test_alnum_and_name_boundary_chars(c):
    lc = c.lower()
    ents = [["e", f"q{lc}"], ["f", "x"]]
    out = check(d(f"q{c} r x", ents, [["r", "r"]]))
    assert len(out["triples"]) == 1
    out = check(d(f"q{c}{c} r x", ents, [["r", "r"]]))
    assert out["triples"] == []
    out = check(d(f"{c}q r x", [["e", "q"], ["f", "x"]], [["r", "r"]]))
    assert out["triples"] == []
    if c.isalpha():
        run(d(ents=[[lc, "x"]], rels=[[lc, "x"]]))
        run(d(ents=[["a", "x"]], rels=[[lc * 20, "x"]]))
    for sep in "`{@[/:":
        out = check(d(f"q{sep}r x", [["e", "q"], ["f", "x"]], [["r", "r"]]))
        assert out["triples"] == []
        out = check(d(f"q {sep} x", [["e", "q"], ["f", "x"]], [["r", "r"]]))
        assert out["triples"] == []


def test_single_char_text_and_single_token_text():
    for t in ["a", "A", "9", "Ada", "ACME", "x"]:
        out = check(d(t))
        assert out["triples"] == []
    assert run(d("a"))["sentences_scanned"] == 1
    assert run(d("Ada"))["mentions_found"] == 1


def test_phantom_start_regression_two_mentions_with_longer_phrase():
    ents = [["c", "york"], ["x", "a b c"]]
    out = run(d("york york", ents, [["r", "r"]]))
    assert out["mentions_found"] == 2
    out = check(d("york r york", ents, [["r", "r"]]))
    assert [(t["subject"]["start"], t["object"]["start"]) for t in out["triples"]] == [(0, 7)]
    out = check(d("york york york", ents, [["r", "r"]]))
    assert out["mentions_found"] == 3
