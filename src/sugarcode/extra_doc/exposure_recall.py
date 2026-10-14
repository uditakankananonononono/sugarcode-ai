"""Incidental Learning - exact recall rate by exposure band for words a caller says a learner met in passing.

Pure function over caller data. No network, no clock, no floats, no randomness. Input: words,
1..12 words, each [word, exposures, recalled]: word a label (1..12 characters a-z and _, all
different), exposures an int 1..10 (times met) and recalled the int 1 or 0 (recalled in a later
test). The data key is exactly words.

Bands: "low" is 1 to 2 exposures, "mid" is 3 to 5, "high" is 6 to 10. The result gives "bands",
a dict (keys low, mid, high, always all three) of band -> {"words": n, "recalled": r, "rate":
exact Fraction string or null when the band has no words}; "overall_rate" as an exact Fraction
string; and "rising": true when the rates of the bands that have words never fall from one band
to the next in the order low, mid, high.

Scope: bounded for the Incidental Learning line. Counting over a list the caller wrote. It does
not run a test or say what the learner noticed.

Not claimed: that the exposures happened, that more exposures caused recall, that the bands are
the right ones, or anything about the real world. Every claim flag in the result is False.
"""
import re
from fractions import Fraction

_NAME = re.compile(r"[a-z_]{1,12}\Z")
BANDS = (("low", 1, 2), ("mid", 3, 5), ("high", 6, 10))
NOT_CLAIMED = (
    "the exposures happened",
    "more exposures caused recall",
    "the bands are the right ones",
    "real-world outcome",
)
CLAIMS = {"happened": False, "caused_recall": False, "right_bands": False, "real_world": False}


class ExposureError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"words"}:
        raise ExposureError("data keys must be exactly words")
    v = data["words"]
    if type(v) is not list or not 1 <= len(v) <= 12:
        raise ExposureError("words must be a list of 1 to 12 words")
    seen = set()
    out = []
    for e in v:
        if type(e) is not list or len(e) != 3:
            raise ExposureError("each word must be a list of [word, exposures, recalled]")
        w, x, r = e
        if type(w) is not str or not _NAME.match(w):
            raise ExposureError("word must be 1..12 characters from a-z and _")
        if type(x) is not int or type(r) is not int:
            raise ExposureError("exposures and recalled must be ints")
        if not 1 <= x <= 10:
            raise ExposureError("exposures must be 1 to 10")
        if r not in (0, 1):
            raise ExposureError("recalled must be 0 or 1")
        if w in seen:
            raise ExposureError("words must be distinct")
        seen.add(w)
        out.append((x, r))
    return out


def exposure_recall(data):
    rows = _validate(data)
    bands = {}
    rates = []
    for name, lo, hi in BANDS:
        inside = [r for x, r in rows if lo <= x <= hi]
        rate = Fraction(sum(inside), len(inside)) if inside else None
        bands[name] = {"words": len(inside), "recalled": sum(inside), "rate": None if rate is None else str(rate)}
        if rate is not None:
            rates.append(rate)
    return {
        "status": "completed",
        "bands": bands,
        "overall_rate": str(Fraction(sum(r for _, r in rows), len(rows))),
        "rising": all(rates[i] >= rates[i - 1] for i in range(1, len(rates))),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
