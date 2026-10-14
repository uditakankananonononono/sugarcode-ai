"""Text Classification - exact multinomial Naive Bayes over caller-supplied labelled text.

Pure function over caller data. No retrieval, no network, no clock, no floats, no
randomness, no logarithms. Input: examples, 2..40 [label, text] pairs; text, the string
to classify. A label is 1..10 lower-case ASCII letters; at least two distinct labels
must occur. Every example text and the query text are ASCII of 1..200 characters.
Tokens are maximal runs of ASCII letters and digits, lower-cased.

Method: with N examples, n_l of them labelled l, vocabulary V = the distinct tokens of
all example texts (at least one required), c_lw the count of token w over the examples
of label l and T_l the total token count of label l, the exact score of label l for the
query is  (n_l / N) * product over the query's tokens w in V of (c_lw + 1) / (T_l + V)
(Laplace smoothing, repeats counted). Query tokens outside V are ignored and counted.
Scores are exact Fractions; the posterior of each label is its score divided by the sum
of the scores, so the posteriors sum to exactly 1. The predicted label has the largest
posterior; exact ties go to the alphabetically first label and are flagged.

Scope: PARTIAL for the Text Classification line. Exact Naive Bayes with add-one
smoothing and bag-of-words features over the caller's own examples. It is not a
general classifier: no feature weighting, no n-grams, no learned embeddings.

Not claimed: that the predicted label is correct for the document, that the examples
are representative, that Naive Bayes independence holds, or anything about the real
world. Every claim flag in the result is False.
"""
from fractions import Fraction

MAX_EXAMPLES = 40
MIN_EXAMPLES = 2
MAX_TEXT = 200
MAX_LABEL = 10
_TOP = frozenset({"examples", "text"})

NOT_CLAIMED = (
    "the predicted label is correct for the document",
    "the examples are representative",
    "the Naive Bayes independence assumption holds",
    "real-world outcome",
)
CLAIMS = {"correct": False, "representative": False, "independence": False, "real_world": False}


class ClsError(ValueError):
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


def _text(v, name):
    if not isinstance(v, str):
        raise ClsError(f"{name} must be a string")
    if not 1 <= len(v) <= MAX_TEXT:
        raise ClsError(f"{name} length out of range")
    if not v.isascii():
        raise ClsError(f"{name} must be ASCII")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise ClsError("data keys must be exactly examples, text")
    raw = data["examples"]
    if not isinstance(raw, list) or not MIN_EXAMPLES <= len(raw) <= MAX_EXAMPLES:
        raise ClsError("examples must be a list of 2..40 [label, text] pairs")
    ex = []
    for e in raw:
        if not isinstance(e, list) or len(e) != 2:
            raise ClsError("example must be a [label, text] pair")
        label, t = e
        if not isinstance(label, str):
            raise ClsError("label must be a string")
        if not 1 <= len(label) <= MAX_LABEL or not all("a" <= c <= "z" for c in label):
            raise ClsError("label must be 1..10 lower-case ASCII letters")
        ex.append((label, _text(t, "example text")))
    if len({l for l, _ in ex}) < 2:
        raise ClsError("examples must contain at least two distinct labels")
    return ex, _text(data["text"], "text")


def text_classification(data):
    ex, query = _validate(data)
    labels = sorted({l for l, _ in ex})
    docs = {l: 0 for l in labels}
    counts = {l: {} for l in labels}
    for l, t in ex:
        docs[l] += 1
        for w in _tokens(t):
            counts[l][w] = counts[l].get(w, 0) + 1
    vocab = set()
    for l in labels:
        vocab |= set(counts[l])
    if not vocab:
        raise ClsError("example texts have no tokens")
    total = {l: sum(counts[l].values()) for l in labels}
    qt = _tokens(query)
    used = [w for w in qt if w in vocab]
    score = {}
    for l in labels:
        s = Fraction(docs[l], len(ex))
        for w in used:
            s *= Fraction(counts[l].get(w, 0) + 1, total[l] + len(vocab))
        score[l] = s
    z = sum(score.values())
    post = {l: score[l] / z for l in labels}
    best = max(post.values())
    winners = [l for l in labels if post[l] == best]
    return {
        "status": "completed",
        "predicted": winners[0],
        "tie": len(winners) > 1,
        "posterior": {l: str(post[l]) for l in labels},
        "vocabulary_size": len(vocab),
        "tokens_used": len(used),
        "tokens_ignored": len(qt) - len(used),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
