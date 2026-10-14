"""Stress Management - exact weighted checklist score and band from caller-supplied ratings.

Pure function over caller data. No sensors, no clock, no floats, no randomness. Input:
items, 1..30 [weight, rating] int pairs with weight 1..10 and rating 0..4 (the caller's
own 0-4 scale); low_below and high_from, ints with 1 <= low_below < high_from <= 100
(percent cut points chosen by the caller).

Score = sum of weight * rating. The maximum is 4 * sum of weights. The share is
score / maximum as an exact Fraction string. Band: "low" when the share is below
low_below percent, "high" when it is at or above high_from percent, otherwise "medium"
(boundaries are exact, no rounding).

Scope: bounded implementation for the Stress Management line. Weighted arithmetic on ratings the caller
wrote and cut points the caller chose. It is not a stress test, screening tool or advice.

Not claimed: that the ratings are accurate, that the band means anything clinically, that
the cut points are right, or anything about health or the real world. Every claim flag in
the result is False.
"""
from fractions import Fraction

MAX_ITEMS = 30
_TOP = frozenset({"items", "low_below", "high_from"})

NOT_CLAIMED = (
    "the ratings are accurate",
    "the band means anything clinically",
    "the cut points are right",
    "health or real-world outcome",
)
CLAIMS = {"accurate_ratings": False, "clinical": False, "cut_points_valid": False, "health_claim": False}


class StressError(ValueError):
    pass


def _int(v, lo, hi, name):
    if type(v) is not int:
        raise StressError(f"{name} must be an int")
    if v < lo or v > hi:
        raise StressError(f"{name} out of range")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise StressError("data keys must be exactly high_from, items, low_below")
    raw = data["items"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_ITEMS:
        raise StressError("items must be a list of 1..30 [weight, rating] pairs")
    items = []
    for p in raw:
        if not isinstance(p, list) or len(p) != 2:
            raise StressError("item must be a [weight, rating] pair")
        items.append((_int(p[0], 1, 10, "weight"), _int(p[1], 0, 4, "rating")))
    lo = _int(data["low_below"], 1, 100, "low_below")
    hi = _int(data["high_from"], 1, 100, "high_from")
    if lo >= hi:
        raise StressError("low_below must be below high_from")
    return items, lo, hi


def stress_score(data):
    items, lo, hi = _validate(data)
    score = sum(w * r for w, r in items)
    top = 4 * sum(w for w, _ in items)
    share = Fraction(score, top)
    band = "low" if share * 100 < lo else "high" if share * 100 >= hi else "medium"
    return {
        "status": "completed",
        "score": score,
        "maximum": top,
        "share": str(share),
        "band": band,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
