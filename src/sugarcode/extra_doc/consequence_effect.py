"""Operant Conditioning - exact effect of each consequence on the next interval's behaviour count.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
intervals, 2..12 intervals in time order, each [count, consequence]: count an int 0..50 (how
often the behaviour occurred in the interval) and consequence one of the strings reward,
punish, none (what followed that interval). The data key is exactly intervals.

For each neighbouring pair of intervals, the change is the later count minus the earlier
count, and it is credited to the consequence of the earlier interval (the last interval's
consequence has no later interval and is not used). The result gives "effects": a dict of
consequence -> {"transitions": n, "mean_change": exact Fraction string} for each consequence
that was credited at least once (keys sorted); "increasing": the consequences with a mean
change above 0 (sorted); "decreasing": those with a mean change below 0 (sorted).

Scope: bounded implementation for the Operant Conditioning line. Arithmetic on interval counts the caller
wrote. It does not condition anyone or show that a consequence caused a change.

Not claimed: that the counts are real behaviour, that a consequence caused the change, that
the next interval is the right window, or anything about the real world. Every claim flag in
the result is False.
"""
from fractions import Fraction

_KINDS = ("reward", "punish", "none")
NOT_CLAIMED = (
    "the counts are real behaviour",
    "a consequence caused the change",
    "the next interval is the right window",
    "real-world outcome",
)
CLAIMS = {"real_behaviour": False, "caused": False, "right_window": False, "real_world": False}


class OperantError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"intervals"}:
        raise OperantError("data keys must be exactly intervals")
    v = data["intervals"]
    if type(v) is not list or not 2 <= len(v) <= 12:
        raise OperantError("intervals must be a list of 2 to 12 intervals")
    out = []
    for e in v:
        if type(e) is not list or len(e) != 2:
            raise OperantError("each interval must be a list of [count, consequence]")
        c, k = e
        if type(c) is not int:
            raise OperantError("count must be an int")
        if not 0 <= c <= 50:
            raise OperantError("count must be 0 to 50")
        if type(k) is not str or k not in _KINDS:
            raise OperantError("consequence must be one of reward, punish, none")
        out.append((c, k))
    return out


def consequence_effect(data):
    iv = _validate(data)
    sums = {}
    for i in range(len(iv) - 1):
        k = iv[i][1]
        n, t = sums.get(k, (0, 0))
        sums[k] = (n + 1, t + iv[i + 1][0] - iv[i][0])
    effects = {}
    means = {}
    for k in sorted(sums):
        n, t = sums[k]
        means[k] = Fraction(t, n)
        effects[k] = {"transitions": n, "mean_change": str(means[k])}
    return {
        "status": "completed",
        "effects": effects,
        "increasing": sorted(k for k in means if means[k] > 0),
        "decreasing": sorted(k for k in means if means[k] < 0),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
