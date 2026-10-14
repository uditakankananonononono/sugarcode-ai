"""Sleep Hygiene - exact sleep-duration and bedtime-regularity tallies from caller-supplied nights.

Pure function over caller data. No sensors, no clock, no floats, no randomness. Input:
nights, 1..60 [bedtime, waketime] int pairs, minutes after midnight 0..1439, with bedtime
different from waketime; target, an int 60..1440 (minutes of sleep the caller aims for).

Duration of a night is (waketime - bedtime) mod 1440 minutes, so a night that crosses
midnight counts correctly and the wake time is always the next occurrence after bedtime.
The result gives the durations; the mean duration as an exact Fraction string; the number
of nights at or above the target; the shortest and longest duration; and the bedtime
spread: bedtimes are measured as minutes after 12:00 noon ((bedtime - 720) mod 1440) so
late-evening and after-midnight bedtimes sit on one line, and the spread is the largest
minus the smallest of those values.

Scope: PARTIAL for the Sleep Hygiene line. Clock arithmetic on times the caller wrote. It
does not track sleep, judge sleep quality, or give health advice. The noon cut for
bedtime spread is a stated convention and fails for bedtimes spread across noon.

Not claimed: that the times are accurate, that the target is right for anyone, that
regularity is healthy, or anything about health or the real world. Every claim flag in the
result is False.
"""
from fractions import Fraction

MAX_NIGHTS = 60
DAY = 1440
_TOP = frozenset({"nights", "target"})

NOT_CLAIMED = (
    "the times are accurate",
    "the target is right for anyone",
    "regularity is healthy",
    "health or real-world outcome",
)
CLAIMS = {"accurate_times": False, "target_valid": False, "regularity_healthy": False, "health_claim": False}


class SleepError(ValueError):
    pass


def _int(v, lo, hi, name):
    if type(v) is not int:
        raise SleepError(f"{name} must be an int")
    if v < lo or v > hi:
        raise SleepError(f"{name} out of range")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise SleepError("data keys must be exactly nights, target")
    raw = data["nights"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_NIGHTS:
        raise SleepError("nights must be a list of 1..60 [bedtime, waketime] pairs")
    out = []
    for p in raw:
        if not isinstance(p, list) or len(p) != 2:
            raise SleepError("night must be a [bedtime, waketime] pair")
        b = _int(p[0], 0, DAY - 1, "bedtime")
        w = _int(p[1], 0, DAY - 1, "waketime")
        if b == w:
            raise SleepError("bedtime and waketime must differ")
        out.append((b, w))
    return out, _int(data["target"], 60, DAY, "target")


def sleep_schedule(data):
    nights, target = _validate(data)
    dur = [(w - b) % DAY for b, w in nights]
    shifted = [(b - 720) % DAY for b, _ in nights]
    return {
        "status": "completed",
        "durations": dur,
        "mean_duration": str(Fraction(sum(dur), len(dur))),
        "nights_at_target": sum(1 for x in dur if x >= target),
        "shortest": min(dur),
        "longest": max(dur),
        "bedtime_spread": max(shifted) - min(shifted),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
