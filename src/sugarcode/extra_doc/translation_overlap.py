"""Row 558 machine translation (PARTIAL): clipped n-gram overlap between a candidate translation and a reference.

reference and candidate are strings of up to 2000 characters with 1 to 200 words each (whitespace split,
lower-cased, punctuation kept as part of a word). overlap(reference, candidate) returns the modified (clipped)
precision for n = 1 and n = 2, as exact Fractions: the number of candidate n-grams counted at most as often as they
occur in the reference, divided by the number of candidate n-grams (None for n = 2 when the candidate has a single
word). It also returns the length ratio candidate words / reference words. This is a surface overlap score of the
BLEU family; it does not translate anything and it cannot tell a correct paraphrase from a wrong sentence."""
from fractions import Fraction

MAX_CHARS = 2000
MAX_WORDS = 200
STATUS_NOTE = ("PARTIAL: clipped unigram and bigram overlap with one reference only; no translation, no "
               "judgment of meaning or fluency")


def _words(text, name):
    if not isinstance(text, str):
        raise ValueError(f"{name}: string required")
    if len(text) > MAX_CHARS:
        raise ValueError(f"{name}: at most {MAX_CHARS} characters")
    words = text.lower().split()
    if not words:
        raise ValueError(f"{name}: at least 1 word required")
    if len(words) > MAX_WORDS:
        raise ValueError(f"{name}: at most {MAX_WORDS} words")
    return words


def _grams(words, n):
    out = {}
    for i in range(len(words) - n + 1):
        g = tuple(words[i:i + n])
        out.setdefault(g, []).append(i)
    return {g: len(pos) for g, pos in out.items()}


def _precision(ref, cand, n):
    cg = _grams(cand, n)
    total = sum(cg.values())
    if total == 0:
        return None
    rg = _grams(ref, n)
    hit = sum(min(c, rg.get(g, 0)) for g, c in cg.items())
    return Fraction(hit, total)


def overlap(reference, candidate):
    ref = _words(reference, "reference")
    cand = _words(candidate, "candidate")
    return {"precision_1": _precision(ref, cand, 1), "precision_2": _precision(ref, cand, 2),
            "length_ratio": Fraction(len(cand), len(ref)), "status_note": STATUS_NOTE}
