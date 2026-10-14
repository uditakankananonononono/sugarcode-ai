"""Mindfulness - exact tallies over a caller-supplied string of present/drifted check-ins.

Pure function over caller data. No sensors, no clock, no floats, no randomness. Input:
checkins, a string of 1..500 characters, each P (present) or D (mind had drifted).

The result gives the length, present and drifted counts, the present share as an exact
Fraction string, the number of drifts (a P followed directly by D), the number of returns
(a D followed directly by P), the longest run of P, and the mean length of the P runs as an
exact Fraction string (null when there is no P).

Scope: PARTIAL for the Mindfulness line. Counting on a string the caller wrote. It does
not measure awareness, teach, or advise.

Not claimed: that the check-ins are accurate, that the tallies reflect mindfulness, that
they predict anything, or anything about health or the real world. Every claim flag in
the result is False.
"""
from fractions import Fraction

MAX_LEN = 500
_TOP = frozenset({"checkins"})

NOT_CLAIMED = (
    "the check-ins are accurate",
    "the tallies reflect mindfulness",
    "the tallies predict anything",
    "health or real-world outcome",
)
CLAIMS = {"accurate_checkins": False, "measures_mindfulness": False, "predictive": False, "health_claim": False}


class AttentionError(ValueError):
    pass


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise AttentionError("data keys must be exactly checkins")
    s = data["checkins"]
    if not type(s) is str or not 1 <= len(s) <= MAX_LEN:
        raise AttentionError("checkins must be a string of 1..500 characters")
    if any(c not in "PD" for c in s):
        raise AttentionError("checkins must use only P and D")
    return s


def attention_log(data):
    s = _validate(data)
    runs = []
    cur = 0
    for c in s:
        if c == "P":
            cur += 1
        elif cur:
            runs.append(cur)
            cur = 0
    if cur:
        runs.append(cur)
    present = s.count("P")
    return {
        "status": "completed",
        "length": len(s),
        "present": present,
        "drifted": len(s) - present,
        "present_share": str(Fraction(present, len(s))),
        "drifts": sum(1 for a, b in zip(s, s[1:]) if a == "P" and b == "D"),
        "returns": sum(1 for a, b in zip(s, s[1:]) if a == "D" and b == "P"),
        "longest_present_run": max(runs) if runs else 0,
        "mean_present_run": str(Fraction(sum(runs), len(runs))) if runs else None,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
