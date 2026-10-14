import copy
import random
import re
from fractions import Fraction

import pytest

from sugarcode.extra_doc import topic_modeling as m
from sugarcode.extra_doc.topic_modeling import TopicError, topic_modeling as run

F = Fraction
KEYS = "data keys must be exactly documents, min_df, link"
STOP = set(m.STOP_WORDS)
DOCS = [
    "apple banana cherry",
    "apple banana",
    "banana cherry apple pie",
    "rocket engine launch",
    "rocket launch pad",
    "launch engine rocket the pad",
]


def d(docs=None, mdf=2, link=(1, 2)):
    return {"documents": list(DOCS if docs is None else docs), "min_df": mdf, "link": list(link)}


def bad(data, msg):
    with pytest.raises(TopicError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(data):
    """Independent: regex tokens, plain dict of sets, breadth-first components, brute-force counting."""
    docs = [set(w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP) for s in data["documents"]]
    df = {}
    for i, ts in enumerate(docs):
        for w in ts:
            df.setdefault(w, set()).add(i)
    kept = sorted(w for w in df if len(df[w]) >= data["min_df"])
    thr = F(*data["link"])
    adj = {w: [v for v in kept if v != w and F(len(df[w] & df[v]), len(df[w] | df[v])) >= thr] for w in kept}
    seen, comps = set(), []
    for w in kept:
        if w in seen:
            continue
        comp, queue = [], [w]
        seen.add(w)
        while queue:
            x = queue.pop(0)
            comp.append(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    queue.append(y)
        comps.append(sorted(comp))
    comps.sort(key=lambda c: (-len(c), c[0]))
    topics = [{"terms": c, "documents": sorted(i for i, ts in enumerate(docs) if ts & set(c))} for c in comps]
    assign = []
    for ts in docs:
        counts = [len(ts & set(c)) for c in comps]
        top = max(counts, default=0)
        assign.append(counts.index(top) if top > 0 else None)
    return topics, assign, len(kept)


def check(data):
    out = run(data)
    t, a, n = oracle(data)
    assert out["topics"] == t and out["assignments"] == a and out["terms_kept"] == n
    return out


def test_basic():
    out = check(d())
    assert out["topics"][0]["terms"] == ["engine", "launch", "pad", "rocket"]
    assert out["topics"][1]["terms"] == ["apple", "banana", "cherry"]
    assert out["topics"][0]["documents"] == [3, 4, 5] and out["topics"][1]["documents"] == [0, 1, 2]
    assert out["assignments"] == [1, 1, 1, 0, 0, 0]
    assert out["terms_kept"] == 7
    assert out["status"] == "completed"
    assert out["claims"] == {"meaningful": False, "exhaustive": False, "threshold_tuned": False, "real_world": False}
    assert len(out["not_claimed"]) == 4


def test_link_threshold_boundary_exact():
    docs = ["a1 b1", "a1 b1", "a1", "b1 c1", "c1"]    # J(a1,b1)=2/3 (docs{0,1,2} vs {0,1,3}: inter 2, union 4 -> 1/2)
    out = check(d(docs, 1, (1, 2)))
    assert ["a1", "b1"] in [t["terms"] for t in out["topics"]]
    out = check(d(docs, 1, (51, 100)))
    assert ["a1"] in [t["terms"] for t in out["topics"]] and ["b1"] in [t["terms"] for t in out["topics"]]
    out = check(d(docs, 1, (1, 1)))
    assert all(len(t["terms"]) == 1 for t in out["topics"])
    out = check(d(["x1 y1", "x1 y1"], 1, (1, 1)))
    assert out["topics"][0]["terms"] == ["x1", "y1"]


def test_min_df_filters_and_singletons():
    out = check(d(DOCS, 3))
    assert out["terms_kept"] == 4          # apple, banana, rocket, launch
    out = check(d(DOCS, 1, (100, 100)))
    assert all(len(t["terms"]) >= 1 for t in out["topics"])
    out = check(d(["solo words", "other things"], 2))
    assert out["topics"] == [] and out["assignments"] == [None, None] and out["terms_kept"] == 0


def test_topic_order_and_assignment_ties():
    docs = ["m1 n1", "m1 n1", "p1 q1", "p1 q1", "m1 p1"]
    out = check(d(docs, 2, (2, 3)))
    assert [t["terms"] for t in out["topics"]] == [["m1", "n1"], ["p1", "q1"]]
    assert out["assignments"][4] == 0           # one term from each topic: tie goes to the lowest index
    docs = ["zz1 yy1 ww1", "zz1 yy1 ww1", "aa1 bb1", "aa1 bb1"]
    out = check(d(docs, 2, (1, 1)))
    assert [t["terms"] for t in out["topics"]] == [["ww1", "yy1", "zz1"], ["aa1", "bb1"]]


def test_stop_words_dropped():
    out = check(d(["the of and apple", "the of and apple"], 2))
    assert out["terms_kept"] == 1
    for w in sorted(STOP):
        out = run(d([w + " kiwi", w + " kiwi"], 2))
        assert out["terms_kept"] == 1
    assert len(STOP) == 32 and "apple" not in STOP


def test_tokenization_boundaries():
    for c in "aAzZ09":
        lc = c.lower()
        out = check(d([f"q{c} x1", f"Q{c}, y1"], 2))
        assert out["terms_kept"] == 1 and out["topics"][0]["terms"] == ["q" + lc]
    for sep in "`{@[/:":
        out = check(d([f"qq{sep}rr", f"qq {sep} rr"], 2))
        assert out["terms_kept"] == 2


def test_random_against_oracle():
    rng = random.Random(13)
    words = ["red", "blue", "sun", "moon", "x1", "Red", "the", "star", "y2"]
    for _ in range(300):
        docs = [" ".join(rng.choice(words) for _ in range(rng.randint(1, 6))) for _ in range(rng.randint(2, 8))]
        n = rng.randint(1, 4)
        check(d(docs, rng.randint(1, 3), (n, rng.randint(n, 5))))


def test_term_cap_boundary():
    # exactly 200 kept terms is accepted, 201 is refused (each term appears in both documents)
    # 300 chars hold 60 five-char tokens, so build 200 terms across 4 documents of 50 tokens each, each doc twice
    parts = [" ".join("k%03d" % i for i in range(j * 50, (j + 1) * 50)) for j in range(4)]
    assert all(len(x) <= 300 for x in parts)
    assert run(d(parts + parts, 2))["terms_kept"] == 200
    parts2 = parts[:3] + [" ".join("k%03d" % i for i in range(150, 201))[:300]]
    assert len(parts2[3].split()) == 51 and len(parts2[3]) <= 300
    bad(d(parts2 + parts2, 2), "too many terms after min_df filtering")


def test_too_many_terms_error():
    # 30 docs x 300 chars, each repeated in two docs: 5 tokens of 5 chars per 30 chars -> far above 200 kept terms
    toks = ["k%04d" % i for i in range(1000)]
    docs = []
    for i in range(30):
        chunk = toks[i * 34:(i + 1) * 34]
        docs.append(" ".join(chunk)[:300])
    docs = docs + []
    docs2 = docs[:15] + docs[:15]
    bad(d(docs2, 2), "too many terms after min_df filtering")


def test_caps_and_boundaries():
    run(d(["a1" * 150, "b1"]))
    bad(d(["a" * 301, "b"]), "document length out of range")
    bad(d(["a" * 10**6, "b"]), "document length out of range")
    bad(d(["", "b"]), "document length out of range")
    run(d(["x1 y1"] * 30))
    bad(d(["x1"] * 31), "documents must be a list of 2..30 strings")
    bad(d(["x1"] * 10**5), "documents must be a list of 2..30 strings")
    bad(d(["x1"]), "documents must be a list of 2..30 strings")
    bad(d([]), "documents must be a list of 2..30 strings")
    run(d(mdf=30))
    run(d(mdf=1))
    bad(d(mdf=31), "min_df must be in 1..30")
    bad(d(mdf=0), "min_df must be in 1..30")
    bad(d(mdf=-1), "min_df must be in 1..30")
    run(d(link=(100, 100)))
    run(d(link=(1, 100)))
    bad(d(link=(1, 101)), "link must satisfy 1 <= n <= d <= 100")
    bad(d(link=(0, 1)), "link must satisfy 1 <= n <= d <= 100")
    bad(d(link=(2, 1)), "link must satisfy 1 <= n <= d <= 100")
    bad(d(link=(-1, 2)), "link must satisfy 1 <= n <= d <= 100")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, [], {}, b"a"])
def test_nonstring_documents(v):
    bad(d(["a1", v]), "document must be a string")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a", "b")])
def test_noncontainer_documents(v):
    x = d()
    x["documents"] = v
    bad(x, "documents must be a list of 2..30 strings")


@pytest.mark.parametrize("v", [True, False, 1.0, 2.5, None, "2", [2], {}])
def test_nonint_min_df(v):
    x = d()
    x["min_df"] = v
    bad(x, "min_df must be an int")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "12", {}, [1], [1, 2, 3], (1, 2)])
def test_bad_link_shape(v):
    x = d()
    x["link"] = v
    bad(x, "link must be an [n, d] pair")


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1]])
def test_link_entry_types(v):
    for pair in ([v, 2], [1, v]):
        x = d()
        x["link"] = pair
        bad(x, "link entries must be ints")


def test_ascii_only():
    bad(d(["caf\u00e9", "b"]), "document must be ASCII")
    bad(d(["\u0661", "b"]), "document must be ASCII")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("documents", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("documents", "min_df", "link"):
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
    a["claims"]["meaningful"] = True
    a["topics"][0]["terms"].append("zz")
    r = run(x)
    assert r["claims"]["meaningful"] is False and "zz" not in r["topics"][0]["terms"]
    assert m.CLAIMS["meaningful"] is False
