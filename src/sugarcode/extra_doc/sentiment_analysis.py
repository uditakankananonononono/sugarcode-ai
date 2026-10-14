"""Sentiment Analysis - exact lexicon-weighted polarity of caller-supplied text.

Pure function over caller data. No retrieval, no network, no clock, no floats, no
randomness, no model. Input: text, ASCII of 1..2000 characters made of printable
characters, newline and tab; lexicon, 1..100 [word, weight] pairs with a word of 1..20
lower-case letters or digits and an integer weight -5..5, not 0; negators, 0..10 words
of the same shape. Lexicon words and negators must be distinct from each other.

Method: the text is split into tokens (maximal runs of ASCII letters and digits,
lower-cased) with character offsets. Each token found in the lexicon contributes its
weight; if the token immediately before it is a negator and only spaces and tabs
separate them, the contribution is the negated weight. Only that one preceding token is
looked at, so "not not good" is negated once. The result gives the exact integer score,
positive and negative totals, the label (positive when the score is above 0, negative
when below 0, otherwise neutral), the token count, the exact score per token as a
Fraction string, and every matched token with its offsets.

Scope: PARTIAL for the Sentiment Analysis line. Exact polarity arithmetic over a
caller-supplied lexicon with one-token negation. It is not a trained sentiment model:
no sarcasm, no intensifiers, no multi-word phrases, no emoji, no context beyond the one
preceding token.

Not claimed: that the label matches what a human reader would feel, that words absent
from the lexicon are neutral, that the lexicon weights are right, or anything about the
real world. Every claim flag in the result is False.
"""
from fractions import Fraction

MAX_TEXT = 2000
MAX_LEX = 100
MAX_NEG = 10
MAX_WORD = 20
MAX_WEIGHT = 5
_TOP = frozenset({"text", "lexicon", "negators"})

NOT_CLAIMED = (
    "the label matches what a human reader would feel",
    "words absent from the lexicon are neutral",
    "the lexicon weights are right",
    "real-world outcome",
)
CLAIMS = {"human_agreement": False, "absent_is_neutral": False, "weights_validated": False, "real_world": False}


class SentError(ValueError):
    pass


def _alnum(c):
    return ("a" <= c <= "z") or ("A" <= c <= "Z") or ("0" <= c <= "9")


def _word_ok(w):
    return 1 <= len(w) <= MAX_WORD and all(("a" <= c <= "z") or ("0" <= c <= "9") for c in w)


def _tokens(s):
    out, i, n = [], 0, len(s)
    while i < n:
        if _alnum(s[i]):
            j = i
            while j < n and _alnum(s[j]):
                j += 1
            out.append((s[i:j].lower(), i, j))
            i = j
        else:
            i += 1
    return out


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise SentError("data keys must be exactly text, lexicon, negators")
    text = data["text"]
    if not isinstance(text, str):
        raise SentError("text must be a string")
    if not 1 <= len(text) <= MAX_TEXT:
        raise SentError("text length out of range")
    if not text.isascii():
        raise SentError("text must be ASCII")
    for c in text:
        if (ord(c) < 32 and c not in "\n\t") or ord(c) == 127:
            raise SentError("text has a disallowed control character")
    raw = data["lexicon"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_LEX:
        raise SentError("lexicon must be a list of 1..100 [word, weight] pairs")
    lex = {}
    for e in raw:
        if not isinstance(e, list) or len(e) != 2:
            raise SentError("lexicon entry must be a [word, weight] pair")
        w, wt = e
        if not isinstance(w, str):
            raise SentError("lexicon word must be a string")
        if not _word_ok(w):
            raise SentError("word must be 1..20 lower-case letters or digits")
        if isinstance(wt, bool) or not isinstance(wt, int):
            raise SentError("weight must be an int")
        if wt == 0 or wt < -MAX_WEIGHT or wt > MAX_WEIGHT:
            raise SentError("weight must be a nonzero int in -5..5")
        if w in lex:
            raise SentError("lexicon words must be distinct")
        lex[w] = wt
    nraw = data["negators"]
    if not isinstance(nraw, list) or len(nraw) > MAX_NEG:
        raise SentError("negators must be a list of 0..10 words")
    neg = set()
    for w in nraw:
        if not isinstance(w, str):
            raise SentError("negator must be a string")
        if not _word_ok(w):
            raise SentError("word must be 1..20 lower-case letters or digits")
        if w in neg:
            raise SentError("negators must be distinct")
        if w in lex:
            raise SentError("negators must not be lexicon words")
        neg.add(w)
    return text, lex, neg


def sentiment_analysis(data):
    text, lex, neg = _validate(data)
    toks = _tokens(text)
    matched, pos, ng = [], 0, 0
    for i, (w, s, e) in enumerate(toks):
        if w not in lex:
            continue
        negated = i > 0 and toks[i - 1][0] in neg and all(c in " \t" for c in text[toks[i - 1][2]:s])
        eff = -lex[w] if negated else lex[w]
        if eff > 0:
            pos += eff
        else:
            ng += eff
        matched.append({"word": w, "weight": lex[w], "negated": negated, "effective": eff, "start": s, "end": e})
    score = pos + ng
    label = "positive" if score > 0 else "negative" if score < 0 else "neutral"
    return {
        "status": "completed",
        "score": score,
        "positive_total": pos,
        "negative_total": ng,
        "label": label,
        "token_count": len(toks),
        "score_per_token": str(Fraction(score, len(toks))) if toks else "0",
        "matched": matched,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
