"""Row 720 Diplomatic Language : find caller-listed words in a text, whole-word and case-insensitive for ASCII.

text is a str of 0..2000 characters. avoid is a tuple of 1..20 distinct words (after lowercasing), each 1..20
characters of a-z (ASCII only, lowercase). Words in text are the maximal runs of ASCII letters a-z/A-Z; every
other character (digits, spaces, punctuation, non-ASCII letters) separates words. Each word is lowercased and
compared with the avoid words for equality. The result lists (word_index, avoid_word) for every hit in order and
the count per avoid word. These ranges are this module's own choices. It is a plain list lookup: it does not know
what offends anyone, handles no phrases, spelling variants, other scripts or context, and does not judge a text
diplomatic or safe."""
import re

MAX_TEXT = 2000
MAX_AVOID = 20
NOT_CLAIMED = ("what offends any person", "phrases or context", "other scripts or spelling variants",
               "diplomatic quality of the text", "safety of sending the text")
_WORD = re.compile(r"[a-z]{1,20}")
_RUN = re.compile(r"[A-Za-z]+")


def scan(text, avoid):
    if type(text) is not str or len(text) > MAX_TEXT:
        raise ValueError(f"text: str of 0 to {MAX_TEXT} characters required")
    if type(avoid) is not tuple or not 1 <= len(avoid) <= MAX_AVOID:
        raise ValueError(f"avoid: tuple of 1 to {MAX_AVOID} words required")
    for i, w in enumerate(avoid):
        if type(w) is not str or _WORD.fullmatch(w) is None:
            raise ValueError(f"avoid[{i}]: word of 1 to 20 lowercase a-z letters required")
    if len(set(avoid)) != len(avoid):
        raise ValueError("avoid: words must be distinct")
    hits = []
    for n, run in enumerate(_RUN.findall(text)):
        low = run.lower()
        if low in avoid:
            hits.append((n, low))
    counts = {w: sum(1 for _, h in hits if h == w) for w in avoid}
    return {"hits": hits, "counts": counts, "avoid_terms_validated": False, "not_claimed": NOT_CLAIMED}
