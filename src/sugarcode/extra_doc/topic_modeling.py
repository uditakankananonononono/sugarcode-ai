"""Topic Modeling - exact co-occurrence topic discovery over caller-supplied documents.

Pure function over caller data. No retrieval, no network, no clock, no floats, no
randomness, no sampling. Input: documents, 2..30 ASCII strings of 1..300 characters;
min_df, an int 1..30; link, an [n, d] integer pair read as the rational n/d with
1 <= n <= d <= 100.

Method: tokens are maximal runs of ASCII letters and digits, lower-cased, minus the
fixed stop words below. A term is kept when it occurs in at least min_df documents; at
most 200 kept terms are accepted. Two kept terms are linked when the Jaccard similarity
of their document sets, |A & B| / |A | B| as an exact Fraction, is at least link. A
topic is a connected component of the link graph (a single unlinked term is a topic of
one). Topics are ordered by size descending, then by their first term; the terms inside
a topic are sorted. Each topic reports the documents containing any of its terms. Each
document is assigned the topic with the most of its distinct terms (ties to the lowest
topic index), or None when it has none.

Scope: bounded implementation for the Topic Modeling line. Exact deterministic theme discovery from
term co-occurrence in the caller's documents. It is not LDA or any probabilistic topic
model: no latent variables, no mixtures, no inference.

Not claimed: that a topic is a human-meaningful theme, that the documents have no other
themes, that the link threshold is the right one, or anything about the real world.
Every claim flag in the result is False.
"""
from fractions import Fraction

MAX_DOCS = 30
MIN_DOCS = 2
MAX_DOC = 300
MAX_TERMS = 200
MAX_DEN = 100
_TOP = frozenset({"documents", "min_df", "link"})
STOP_WORDS = frozenset(
    "a an and are as at be by do does for from how in is it of on or that the this to was what when where which who whom why with".split()
)

NOT_CLAIMED = (
    "a topic is a human-meaningful theme",
    "the documents have no other themes",
    "the link threshold is the right one",
    "real-world outcome",
)
CLAIMS = {"meaningful": False, "exhaustive": False, "threshold_tuned": False, "real_world": False}


class TopicError(ValueError):
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
        raise TopicError("data keys must be exactly documents, min_df, link")
    docs = data["documents"]
    if not isinstance(docs, list) or not MIN_DOCS <= len(docs) <= MAX_DOCS:
        raise TopicError("documents must be a list of 2..30 strings")
    for s in docs:
        if not isinstance(s, str):
            raise TopicError("document must be a string")
        if not 1 <= len(s) <= MAX_DOC:
            raise TopicError("document length out of range")
        if not s.isascii():
            raise TopicError("document must be ASCII")
    mdf = data["min_df"]
    if isinstance(mdf, bool) or not isinstance(mdf, int):
        raise TopicError("min_df must be an int")
    if not 1 <= mdf <= MAX_DOCS:
        raise TopicError("min_df must be in 1..30")
    lk = data["link"]
    if not isinstance(lk, list) or len(lk) != 2:
        raise TopicError("link must be an [n, d] pair")
    for v in lk:
        if isinstance(v, bool) or not isinstance(v, int):
            raise TopicError("link entries must be ints")
    if not 1 <= lk[0] <= lk[1] <= MAX_DEN:
        raise TopicError("link must satisfy 1 <= n <= d <= 100")
    return docs, mdf, Fraction(lk[0], lk[1])


def topic_modeling(data):
    docs, mdf, thr = _validate(data)
    doc_terms = [set(t for t in _tokens(s) if t not in STOP_WORDS) for s in docs]
    sets = {}
    for i, ts in enumerate(doc_terms):
        for t in ts:
            sets.setdefault(t, set()).add(i)
    terms = sorted(t for t, ds in sets.items() if len(ds) >= mdf)
    if len(terms) > MAX_TERMS:
        raise TopicError("too many terms after min_df filtering")
    parent = {t: t for t in terms}

    def find(t):
        while parent[t] != t:
            parent[t] = parent[parent[t]]
            t = parent[t]
        return t

    for i, a in enumerate(terms):
        for b in terms[i + 1:]:
            if Fraction(len(sets[a] & sets[b]), len(sets[a] | sets[b])) >= thr:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[max(ra, rb)] = min(ra, rb)
    groups = {}
    for t in terms:
        groups.setdefault(find(t), []).append(t)
    topics = sorted((sorted(g) for g in groups.values()), key=lambda g: (-len(g), g[0]))
    out_topics = []
    for g in topics:
        ds = sorted(set().union(*[sets[t] for t in g]))
        out_topics.append({"terms": g, "documents": ds})
    assign = []
    for ts in doc_terms:
        best, bi = 0, None
        for k, g in enumerate(topics):
            c = sum(1 for t in g if t in ts)
            if c > best:
                best, bi = c, k
        assign.append(bi)
    return {
        "status": "completed",
        "topics": out_topics,
        "assignments": assign,
        "terms_kept": len(terms),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
