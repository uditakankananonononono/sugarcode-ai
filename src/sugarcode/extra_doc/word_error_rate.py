"""Row 556 speech recognition (PARTIAL): scoring a transcript against a reference by word error rate.

reference and hypothesis are strings of up to 5000 characters. Words are the pieces left by splitting on
whitespace and are compared after lower-casing (punctuation is part of a word). The reference needs 1 to 400
words; the hypothesis 0 to 400. distance is the word-level edit distance (insertions, deletions and substitutions
each cost 1) and wer is distance / reference words as an exact Fraction (it can be above 1 when the hypothesis has
many extra words). This scores a transcript someone already has; it does not listen to audio or recognise speech,
and a low error rate on one sample says nothing about other voices, accents or noise."""
from fractions import Fraction

MAX_CHARS = 5000
MAX_WORDS = 400
STATUS_NOTE = ("PARTIAL: word-level edit distance between two supplied transcripts only; no audio, no speech "
               "recognition and no claim about accuracy on other speech")


def _words(text, name, min_words):
    if not isinstance(text, str):
        raise ValueError(f"{name}: string required")
    if len(text) > MAX_CHARS:
        raise ValueError(f"{name}: at most {MAX_CHARS} characters")
    words = text.lower().split()
    if len(words) < min_words:
        raise ValueError(f"{name}: at least {min_words} word required")
    if len(words) > MAX_WORDS:
        raise ValueError(f"{name}: at most {MAX_WORDS} words")
    return words


def score(reference, hypothesis):
    ref = _words(reference, "reference", 1)
    hyp = _words(hypothesis, "hypothesis", 0)
    prev = [0]
    for _ in hyp:
        prev.append(prev[-1] + 1)
    for i, rw in enumerate(ref, 1):
        cur = [i]
        for j, hw in enumerate(hyp, 1):
            cost = 0 if rw == hw else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    dist = prev[len(hyp)]
    return {"distance": dist, "reference_words": len(ref), "hypothesis_words": len(hyp),
            "wer": Fraction(dist, len(ref)), "status_note": STATUS_NOTE}
