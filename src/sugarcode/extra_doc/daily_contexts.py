"""Informal Learning - exact split of caller-recorded everyday learning moments across contexts.

Pure function over caller data. No network, no clock, no floats, no randomness. Input: moments,
1..12 moments, each [context, minutes]: context one of the strings home, work, commute, social,
online and minutes an int 1..120. The data key is exactly moments.

The result gives "minutes", a dict of context -> total minutes for each context present (in the
order home, work, commute, social, online); "total"; "shares", context -> minutes over total as an
exact Fraction string (same order); "top", the context with the most minutes (ties go to the
earlier one in that order); and "missing", the contexts with no moment (same order).

Scope: bounded for the Informal Learning line. Counting minutes in a list the caller wrote. It
does not observe anyone's day or judge what was learned.

Not claimed: that the moments happened, that minutes mean learning, that these five contexts
cover daily life, or anything about the real world. Every claim flag in the result is False.
"""
from fractions import Fraction

CONTEXTS = ("home", "work", "commute", "social", "online")
NOT_CLAIMED = (
    "the moments happened",
    "minutes mean learning",
    "these five contexts cover daily life",
    "real-world outcome",
)
CLAIMS = {"happened": False, "minutes_are_learning": False, "contexts_cover_life": False, "real_world": False}


class ContextError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"moments"}:
        raise ContextError("data keys must be exactly moments")
    v = data["moments"]
    if type(v) is not list or not 1 <= len(v) <= 12:
        raise ContextError("moments must be a list of 1 to 12 moments")
    out = []
    for e in v:
        if type(e) is not list or len(e) != 2:
            raise ContextError("each moment must be a list of [context, minutes]")
        c, m = e
        if type(c) is not str or c not in CONTEXTS:
            raise ContextError("context must be one of home, work, commute, social, online")
        if type(m) is not int:
            raise ContextError("minutes must be an int")
        if not 1 <= m <= 120:
            raise ContextError("minutes must be 1 to 120")
        out.append((c, m))
    return out


def daily_contexts(data):
    mo = _validate(data)
    tot = {}
    for c, m in mo:
        tot[c] = tot.get(c, 0) + m
    total = sum(tot.values())
    present = [c for c in CONTEXTS if c in tot]
    top = present[0]
    for c in present:
        if tot[c] > tot[top]:
            top = c
    return {
        "status": "completed",
        "minutes": {c: tot[c] for c in present},
        "total": total,
        "shares": {c: str(Fraction(tot[c], total)) for c in present},
        "top": top,
        "missing": [c for c in CONTEXTS if c not in tot],
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
