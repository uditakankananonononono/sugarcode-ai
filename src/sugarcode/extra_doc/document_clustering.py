"""Document Clustering - exact agglomerative clustering of caller documents by Jaccard similarity.

Pure function over caller data. No retrieval, no network, no clock, no floats, no
randomness. Input: documents, 2..20 ASCII strings of 1..300 characters, each holding at
least one token (a maximal run of ASCII letters and digits, lower-cased); linkage, one
of "single", "complete", "average"; threshold, an [n, d] integer pair read as the
rational n/d with 1 <= n <= d <= 100.

Method: each document is the set of its distinct tokens; the similarity of two documents
is the exact Fraction |A & B| / |A | B|. Every document starts as its own cluster. The
similarity of two clusters is, by linkage, the maximum (single), minimum (complete) or
arithmetic mean (average) of the document similarities across the pair. At each step the
pair of clusters with the largest similarity is merged, ties going to the pair with the
smaller (lowest document index of the first cluster, lowest document index of the second
cluster) where the first cluster holds the overall lowest document index; the process
stops when the best similarity is below threshold. Clusters are reported as sorted
index lists ordered by their lowest index, with the merge history (both sides and the
exact similarity), the per-document cluster assignment and each cluster's medoid (the
member with the largest summed similarity to the members, ties to the lowest index).

Scope: PARTIAL for the Document Clustering line. Exact bag-of-words hierarchical
clustering over the caller's own documents. It is not k-means or any learned
clustering: no embeddings, no weighting, no choice of the number of clusters.

Not claimed: that a cluster is a meaningful grouping, that the threshold is well chosen,
that documents in different clusters are unrelated, or anything about the real world.
Every claim flag in the result is False.
"""
from fractions import Fraction

MIN_DOCS = 2
MAX_DOCS = 20
MAX_DOC = 300
MAX_DEN = 100
LINKAGES = ("single", "complete", "average")
_TOP = frozenset({"documents", "linkage", "threshold"})

NOT_CLAIMED = (
    "a cluster is a meaningful grouping",
    "the threshold is well chosen",
    "documents in different clusters are unrelated",
    "real-world outcome",
)
CLAIMS = {"meaningful": False, "threshold_tuned": False, "separation": False, "real_world": False}


class ClusterError(ValueError):
    pass


def _alnum(c):
    return ("a" <= c <= "z") or ("A" <= c <= "Z") or ("0" <= c <= "9")


def _tokens(s):
    out, cur = [], []
    for ch in s:
        if _alnum(ch):
            cur.append(ch.lower())
        elif cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    return out


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise ClusterError("data keys must be exactly documents, linkage, threshold")
    docs = data["documents"]
    if not isinstance(docs, list) or not MIN_DOCS <= len(docs) <= MAX_DOCS:
        raise ClusterError("documents must be a list of 2..20 strings")
    sets = []
    for s in docs:
        if not isinstance(s, str):
            raise ClusterError("document must be a string")
        if not 1 <= len(s) <= MAX_DOC:
            raise ClusterError("document length out of range")
        if not s.isascii():
            raise ClusterError("document must be ASCII")
        toks = set(_tokens(s))
        if not toks:
            raise ClusterError("document has no tokens")
        sets.append(toks)
    link = data["linkage"]
    if not isinstance(link, str) or link not in LINKAGES:
        raise ClusterError("linkage must be single, complete or average")
    th = data["threshold"]
    if not isinstance(th, list) or len(th) != 2:
        raise ClusterError("threshold must be an [n, d] pair")
    for v in th:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ClusterError("threshold entries must be ints")
    if not 1 <= th[0] <= th[1] <= MAX_DEN:
        raise ClusterError("threshold must satisfy 1 <= n <= d <= 100")
    return sets, link, Fraction(th[0], th[1])


def document_clustering(data):
    sets, link, thr = _validate(data)
    n = len(sets)
    sim = [[Fraction(len(sets[i] & sets[j]), len(sets[i] | sets[j])) for j in range(n)] for i in range(n)]

    def csim(a, b):
        vals = [sim[i][j] for i in a for j in b]
        if link == "single":
            return max(vals)
        if link == "complete":
            return min(vals)
        return sum(vals) / len(vals)

    clusters = [[i] for i in range(n)]
    merges = []
    while len(clusters) > 1:
        best = None
        for x in range(len(clusters)):
            for y in range(x + 1, len(clusters)):
                s = csim(clusters[x], clusters[y])
                if best is None or s > best[0]:
                    best = (s, x, y)
        if best[0] < thr:
            break
        s, x, y = best
        merges.append({"left": list(clusters[x]), "right": list(clusters[y]), "similarity": str(s)})
        merged = sorted(clusters[x] + clusters[y])
        clusters = [c for k, c in enumerate(clusters) if k not in (x, y)] + [merged]
        clusters.sort(key=lambda c: c[0])
    assign = [0] * n
    medoids = []
    for k, c in enumerate(clusters):
        for i in c:
            assign[i] = k
        scores = [(-sum(sim[i][j] for j in c), i) for i in c]
        medoids.append(min(scores)[1])
    return {
        "status": "completed",
        "clusters": clusters,
        "merges": merges,
        "assignments": assign,
        "medoids": medoids,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
