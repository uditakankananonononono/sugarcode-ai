"""Intentional Learning - exact adherence of caller-recorded study sessions to the minutes the learner planned.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
sessions, 1..10 sessions in order, each [planned, actual]: two ints 0..240 (minutes planned and
minutes actually studied). The data key is exactly sessions.

A session is met when actual is at least planned. The result gives "met", the number of met
sessions; "planned" and "actual", the total minutes; "adherence", actual divided by planned as an
exact Fraction string (null when planned is 0); "shortfall", the sum over sessions of planned
minus actual where that is above 0; and "longest_met_run", the longest run of consecutive met
sessions.

Scope: PARTIAL for the Intentional Learning line. Arithmetic on minutes the caller wrote. It
does not track anyone's study or judge a plan.

Not claimed: that the minutes are real, that meeting a plan means learning, that the plans were
sensible, or anything about the real world. Every claim flag in the result is False.
"""
from fractions import Fraction

NOT_CLAIMED = (
    "the minutes are real",
    "meeting a plan means learning",
    "the plans were sensible",
    "real-world outcome",
)
CLAIMS = {"real_minutes": False, "met_is_learning": False, "sensible_plans": False, "real_world": False}


class AdherenceError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"sessions"}:
        raise AdherenceError("data keys must be exactly sessions")
    v = data["sessions"]
    if type(v) is not list or not 1 <= len(v) <= 10:
        raise AdherenceError("sessions must be a list of 1 to 10 sessions")
    out = []
    for e in v:
        if type(e) is not list or len(e) != 2:
            raise AdherenceError("each session must be a list of [planned, actual]")
        for x in e:
            if type(x) is not int:
                raise AdherenceError("minutes must be ints")
            if not 0 <= x <= 240:
                raise AdherenceError("minutes must be 0 to 240")
        out.append((e[0], e[1]))
    return out


def study_adherence(data):
    s = _validate(data)
    planned = sum(p for p, _ in s)
    actual = sum(a for _, a in s)
    best = run = 0
    for p, a in s:
        run = run + 1 if a >= p else 0
        if run > best:
            best = run
    return {
        "status": "completed",
        "met": sum(1 for p, a in s if a >= p),
        "planned": planned,
        "actual": actual,
        "adherence": str(Fraction(actual, planned)) if planned else None,
        "shortfall": sum(p - a for p, a in s if p > a),
        "longest_met_run": best,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
