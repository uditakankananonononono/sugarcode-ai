"""Emotional Regulation - exact mean rating change per named strategy from caller-supplied before/after ratings.

Pure function over caller data. No sensors, no clock, no floats, no randomness. Input:
entries, 1..300 dicts with exactly the keys strategy (1..12 characters a-z and _),
before and after (ints 0..10, a feeling-intensity rating the caller recorded). At most 10
distinct strategies.

For each strategy (listed in alphabetical order) the result gives the number of entries,
the exact mean of (after - before) as a Fraction string, and how many entries went down,
stayed equal and went up. It also gives the same mean over all entries.

Scope: PARTIAL for the Emotional Regulation line. Averages of ratings the caller wrote. It
does not measure emotions, compare strategies fairly, or advise.

Not claimed: that the ratings are accurate, that a strategy caused any change, that the
means generalise, or anything about health or the real world. Every claim flag in the
result is False.
"""
import re
from fractions import Fraction

MAX_ENTRIES = 300
MAX_STRATEGIES = 10
_NAME = re.compile(r"[a-z_]{1,12}\Z")
_ENTRY = frozenset({"strategy", "before", "after"})
_TOP = frozenset({"entries"})

NOT_CLAIMED = (
    "the ratings are accurate",
    "a strategy caused any change",
    "the means generalise",
    "health or real-world outcome",
)
CLAIMS = {"accurate_ratings": False, "causal": False, "generalises": False, "health_claim": False}


class MoodError(ValueError):
    pass


def _rating(v, name):
    if type(v) is not int:
        raise MoodError(f"{name} must be an int")
    if v < 0 or v > 10:
        raise MoodError(f"{name} out of range")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise MoodError("data keys must be exactly entries")
    raw = data["entries"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_ENTRIES:
        raise MoodError("entries must be a list of 1..300 entries")
    out = []
    for e in raw:
        if not isinstance(e, dict) or set(e) != _ENTRY:
            raise MoodError("entry keys must be exactly after, before, strategy")
        s = e["strategy"]
        if not type(s) is str or not _NAME.match(s):
            raise MoodError("strategy must be 1..12 characters from a-z and _")
        out.append((s, _rating(e["before"], "before"), _rating(e["after"], "after")))
    if len({s for s, _, _ in out}) > MAX_STRATEGIES:
        raise MoodError("at most 10 distinct strategies")
    return out


def _row(deltas):
    return {
        "entries": len(deltas),
        "mean_change": str(Fraction(sum(deltas), len(deltas))),
        "went_down": sum(1 for x in deltas if x < 0),
        "stayed_equal": sum(1 for x in deltas if x == 0),
        "went_up": sum(1 for x in deltas if x > 0),
    }


def mood_shift(data):
    ent = _validate(data)
    by = {}
    for s, b, a in ent:
        by.setdefault(s, []).append(a - b)
    return {
        "status": "completed",
        "strategies": {s: _row(by[s]) for s in sorted(by)},
        "overall": _row([a - b for _, b, a in ent]),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
