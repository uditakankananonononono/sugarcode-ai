import copy
import itertools
import random
import re
from fractions import Fraction

import pytest

from sugarcode.extra_doc import document_clustering as m
from sugarcode.extra_doc.document_clustering import ClusterError, document_clustering as run

F = Fraction
KEYS = "data keys must be exactly documents, linkage, threshold"
DOCS = ["a1 b1 c1", "a1 b1 c1 d1", "x1 y1 z1", "x1 y1", "q1"]


def d(docs=None, link="single", th=(1, 2)):
    return {"documents": list(DOCS if docs is None else docs), "linkage": link, "threshold": list(th)}


def bad(data, msg):
    with pytest.raises(ClusterError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(data):
    """Independent: frozenset clusters, candidate list sorted by an explicit key, regex tokens."""
    sets = [frozenset(re.findall(r"[a-z0-9]+", s.lower())) for s in data["documents"]]
    n = len(sets)
    j = lambda a, b: F(len(sets[a] & sets[b]), len(sets[a] | sets[b]))
    thr = F(*data["threshold"])
    link = data["linkage"]

    def cs(A, B):
        vals = [j(a, b) for a, b in itertools.product(sorted(A), sorted(B))]
        return {"single": max(vals), "complete": min(vals), "average": sum(vals) / len(vals)}[link]

    cl = {frozenset([i]) for i in range(n)}
    merges = []
    while len(cl) > 1:
        cands = []
        for A, B in itertools.combinations(cl, 2):
            lo, hi = (A, B) if min(A) < min(B) else (B, A)
            cands.append((-cs(A, B), min(lo), min(hi), lo, hi))
        cands.sort(key=lambda t: t[:3])
        ns, _, _, lo, hi = cands[0]
        if -ns < thr:
            break
        merges.append({"left": sorted(lo), "right": sorted(hi), "similarity": str(-ns)})
        cl = (cl - {lo, hi}) | {lo | hi}
    clusters = sorted((sorted(c) for c in cl), key=lambda c: c[0])
    assign = [next(k for k, c in enumerate(clusters) if i in c) for i in range(n)]
    med = []
    for c in clusters:
        tot = {i: sum(j(i, o) for o in c) for i in c}
        top = max(tot.values())
        med.append(min(i for i in c if tot[i] == top))
    return clusters, merges, assign, med


def check(data):
    out = run(data)
    c, mg, a, md = oracle(data)
    assert out["clusters"] == c and out["merges"] == mg and out["assignments"] == a and out["medoids"] == md
    return out


def test_basic_all_linkages():
    for link in ("single", "complete", "average"):
        out = check(d(link=link))
        assert out["clusters"] == [[0, 1], [2, 3], [4]], link
        assert out["assignments"] == [0, 0, 1, 1, 2]
    out = run(d())
    assert out["merges"][0] == {"left": [0], "right": [1], "similarity": "3/4"}
    assert out["merges"][1] == {"left": [2], "right": [3], "similarity": "2/3"}
    assert len(out["merges"]) == 2 and out["medoids"] == [0, 2, 4]
    assert out["status"] == "completed"
    assert out["claims"] == {"meaningful": False, "threshold_tuned": False, "separation": False, "real_world": False}
    assert len(out["not_claimed"]) == 4


def test_linkages_differ_on_chain():
    # chain a-b-c: J(a,b)=J(b,c)=1/2, J(a,c)=1/3
    docs = ["p1 q1 r1", "q1 r1 s1", "r1 s1 t1"]
    # J(0,1)=2/4=1/2, J(1,2)=2/4=1/2, J(0,2)=1/5
    out = check(d(docs, "single", (1, 2)))
    assert out["clusters"] == [[0, 1, 2]]
    out = check(d(docs, "complete", (1, 2)))
    assert out["clusters"] == [[0, 1], [2]]
    out = check(d(docs, "average", (1, 2)))
    assert out["clusters"] == [[0, 1], [2]]
    out = check(d(docs, "average", (7, 20)))     # avg of cluster {0,1} vs {2} = (1/2 + 1/5)/2 = 7/20
    assert out["clusters"] == [[0, 1, 2]] and out["merges"][-1]["similarity"] == "7/20"
    out = check(d(docs, "average", (36, 100)))
    assert out["clusters"] == [[0, 1], [2]]
    out = check(d(docs, "complete", (1, 5)))
    assert out["clusters"] == [[0, 1, 2]] and out["merges"][-1]["similarity"] == "1/5"


def test_threshold_boundary_is_inclusive():
    out = check(d(["a1 b1", "a1 c1"], "single", (1, 3)))
    assert out["clusters"] == [[0, 1]]
    out = check(d(["a1 b1", "a1 c1"], "single", (34, 100)))
    assert out["clusters"] == [[0], [1]] and out["merges"] == []
    out = check(d(["a1", "a1"], "single", (1, 1)))
    assert out["clusters"] == [[0, 1]] and out["merges"][0]["similarity"] == "1"
    out = check(d(["a1", "b1"], "single", (1, 100)))
    assert out["clusters"] == [[0], [1]]


def test_tie_breaking_by_lowest_indices():
    docs = ["a1", "a1", "a1", "a1"]
    out = check(d(docs, "single", (1, 1)))
    assert out["merges"][0]["left"] == [0] and out["merges"][0]["right"] == [1]
    assert out["merges"][1]["left"] == [0, 1] and out["merges"][1]["right"] == [2]
    assert out["clusters"] == [[0, 1, 2, 3]]
    docs = ["x1 y1", "m1 n1", "x1 y1", "m1 n1"]
    out = check(d(docs, "single", (1, 1)))
    assert [(mg["left"], mg["right"]) for mg in out["merges"]] == [([0], [2]), ([1], [3])]
    assert out["clusters"] == [[0, 2], [1, 3]] and out["assignments"] == [0, 1, 0, 1]


def test_medoid_tie_lowest_index_and_choice():
    docs = ["a1 b1", "a1 b1 c1", "a1 b1 c1 d1"]   # middle doc is the medoid
    out = check(d(docs, "single", (1, 3)))
    assert out["clusters"] == [[0, 1, 2]] and out["medoids"] == [1]
    out = check(d(["a1", "a1"], "single", (1, 1)))
    assert out["medoids"] == [0]


def test_tokenization_and_case():
    out = check(d(["Hello, WORLD", "hello world", "other"], "single", (1, 1)))
    assert out["clusters"] == [[0, 1], [2]]
    for c in "aAzZ09":
        lc = c.lower()
        out = check(d([f"q{c}", f"q{lc}", "q"], "single", (1, 1)))
        assert out["clusters"] == [[0, 1], [2]]
        out = check(d([f"{c}q", "q"], "single", (1, 1)))
        assert out["clusters"] == [[0], [1]]
    for sep in "`{@[/:":
        out = check(d([f"q{sep}r", "q r"], "single", (1, 1)))
        assert out["clusters"] == [[0, 1]]


def test_random_against_oracle():
    rng = random.Random(17)
    words = ["red", "blue", "sun", "x1", "moon", "a", "z9"]
    for _ in range(300):
        docs = [" ".join(rng.choice(words) for _ in range(rng.randint(1, 5))) for _ in range(rng.randint(2, 7))]
        n = rng.randint(1, 4)
        check(d(docs, rng.choice(["single", "complete", "average"]), (n, rng.randint(n, 5))))


def test_caps_and_boundaries():
    run(d(["a1 " * 100, "b1"]))
    run(d(["a1" * 150, "b1"]))
    bad(d(["a" * 301, "b"]), "document length out of range")
    bad(d(["a" * 10**6, "b"]), "document length out of range")
    bad(d(["", "b"]), "document length out of range")
    run(d(["x1 y1"] * 20))
    bad(d(["x1"] * 21), "documents must be a list of 2..20 strings")
    bad(d(["x1"] * 10**5), "documents must be a list of 2..20 strings")
    bad(d(["x1"]), "documents must be a list of 2..20 strings")
    bad(d([]), "documents must be a list of 2..20 strings")
    bad(d(["!!!", "a1"]), "document has no tokens")
    run(d(th=(100, 100)))
    run(d(th=(1, 100)))
    bad(d(th=(1, 101)), "threshold must satisfy 1 <= n <= d <= 100")
    bad(d(th=(0, 1)), "threshold must satisfy 1 <= n <= d <= 100")
    bad(d(th=(2, 1)), "threshold must satisfy 1 <= n <= d <= 100")
    bad(d(th=(-1, 2)), "threshold must satisfy 1 <= n <= d <= 100")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, [], {}, b"a", "Single", "mean", "", "single "])
def test_bad_linkage(v):
    bad(d(link=v), "linkage must be single, complete or average")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, [], {}, b"a"])
def test_nonstring_documents(v):
    bad(d(["a1", v]), "document must be a string")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a", "b")])
def test_noncontainer_documents(v):
    x = d()
    x["documents"] = v
    bad(x, "documents must be a list of 2..20 strings")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "12", {}, [1], [1, 2, 3], (1, 2)])
def test_bad_threshold_shape(v):
    x = d()
    x["threshold"] = v
    bad(x, "threshold must be an [n, d] pair")


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1]])
def test_threshold_entry_types(v):
    for pair in ([v, 2], [1, v]):
        x = d()
        x["threshold"] = pair
        bad(x, "threshold entries must be ints")


def test_ascii_only():
    bad(d(["caf\u00e9", "b"]), "document must be ASCII")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("documents", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("documents", "linkage", "threshold"):
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
    a["clusters"][0].append(99)
    r = run(x)
    assert r["claims"]["meaningful"] is False and 99 not in r["clusters"][0]
    assert m.CLAIMS["meaningful"] is False
