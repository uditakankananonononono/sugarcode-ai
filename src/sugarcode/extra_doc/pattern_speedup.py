"""Implicit Learning - exact response-time gap between pattern and non-pattern trials in a caller-recorded task.

Pure function over caller data. No network, no clock, no floats, no randomness. Input: trials,
2..12 trials in order, each [pattern, ms]: pattern the int 1 (the trial followed the hidden
pattern) or 0, and ms an int 100..2000 (response time in milliseconds). The data key is
exactly trials.

The result gives "pattern_trials" and "other_trials" (counts); "pattern_mean" and
"other_mean", the mean response time of each kind as an exact Fraction string (null when that
kind has no trials); "speedup", other_mean minus pattern_mean as an exact Fraction string (null
when either mean is null); and "faster_on_pattern": true when speedup is above 0.

Scope: PARTIAL for the Implicit Learning line. Averages over response times the caller wrote.
It measures nobody's awareness and does not run a task.

Not claimed: that the learner was unaware of the pattern, that a speedup shows learning, that
the times were measured properly, or anything about the real world. Every claim flag in the
result is False.
"""
from fractions import Fraction

NOT_CLAIMED = (
    "the learner was unaware of the pattern",
    "a speedup shows learning",
    "the times were measured properly",
    "real-world outcome",
)
CLAIMS = {"unaware": False, "speedup_is_learning": False, "measured_properly": False, "real_world": False}


class SpeedupError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"trials"}:
        raise SpeedupError("data keys must be exactly trials")
    v = data["trials"]
    if type(v) is not list or not 2 <= len(v) <= 12:
        raise SpeedupError("trials must be a list of 2 to 12 trials")
    out = []
    for e in v:
        if type(e) is not list or len(e) != 2:
            raise SpeedupError("each trial must be a list of [pattern, ms]")
        p, ms = e
        if type(p) is not int or type(ms) is not int:
            raise SpeedupError("pattern and ms must be ints")
        if p not in (0, 1):
            raise SpeedupError("pattern must be 0 or 1")
        if not 100 <= ms <= 2000:
            raise SpeedupError("ms must be 100 to 2000")
        out.append((p, ms))
    return out


def pattern_speedup(data):
    t = _validate(data)
    on = [ms for p, ms in t if p == 1]
    off = [ms for p, ms in t if p == 0]
    pm = Fraction(sum(on), len(on)) if on else None
    om = Fraction(sum(off), len(off)) if off else None
    gap = om - pm if pm is not None and om is not None else None
    return {
        "status": "completed",
        "pattern_trials": len(on),
        "other_trials": len(off),
        "pattern_mean": None if pm is None else str(pm),
        "other_mean": None if om is None else str(om),
        "speedup": None if gap is None else str(gap),
        "faster_on_pattern": gap is not None and gap > 0,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
