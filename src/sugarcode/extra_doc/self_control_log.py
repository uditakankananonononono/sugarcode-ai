"""Self-Control - exact tallies over a caller-supplied log of resisted and given-in impulses.

Pure function over caller data. No sensors, no network, no clock, no floats, no
randomness. Input: events, a list of 1..500 ints, each 1 (resisted) or 0 (gave in).

The result gives the count, resisted and gave-in counts, the resist rate as an exact
Fraction string, the longest run of resisted events, the longest run of gave-in events,
and the run of resisted events at the end of the log (0 if the last event was a give-in).

Scope: PARTIAL for the Self-Control line. Counting on a list the caller wrote. It does not
measure self-control, diagnose anything, or advise.

Not claimed: that the log is accurate, that the rate reflects the person's self-control,
that it predicts anything, or anything about health or the real world. Every claim flag
in the result is False.
"""
from fractions import Fraction

MAX_EVENTS = 500
_TOP = frozenset({"events"})

NOT_CLAIMED = (
    "the log is accurate",
    "the rate reflects the person's self-control",
    "the tallies predict anything",
    "health or real-world outcome",
)
CLAIMS = {"accurate_log": False, "measures_self_control": False, "predictive": False, "health_claim": False}


class LogError(ValueError):
    pass


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise LogError("data keys must be exactly events")
    ev = data["events"]
    if not isinstance(ev, list) or not 1 <= len(ev) <= MAX_EVENTS:
        raise LogError("events must be a list of 1..500 ints")
    for v in ev:
        if type(v) is not int:
            raise LogError("events must be ints")
        if v not in (0, 1):
            raise LogError("events must be 0 or 1")
    return list(ev)


def self_control_log(data):
    ev = _validate(data)
    best = {0: 0, 1: 0}
    run = 0
    prev = None
    for v in ev:
        run = run + 1 if v == prev else 1
        prev = v
        best[v] = max(best[v], run)
    resisted = sum(ev)
    return {
        "status": "completed",
        "count": len(ev),
        "resisted": resisted,
        "gave_in": len(ev) - resisted,
        "resist_rate": str(Fraction(resisted, len(ev))),
        "longest_resisted_run": best[1],
        "longest_gave_in_run": best[0],
        "final_resisted_run": run if prev == 1 else 0,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
