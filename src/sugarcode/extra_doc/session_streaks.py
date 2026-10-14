"""Meditation - exact streak and gap tallies over caller-supplied practice days.

Pure function over caller data. No clock, no sensors, no floats, no randomness. Input:
days, a strictly increasing list of 1..365 ints, each 0..100000 (day numbers on which the
caller logged a practice session).

A streak is a maximal run of consecutive day numbers. The result gives the number of
sessions, the number of streaks, the longest streak length, the current streak (the one
ending at the last logged day), the longest gap (the most days with no session between two
logged days; 0 if none), and the span in days from first to last logged day inclusive.

Scope: bounded implementation for the Meditation line. Counting on day numbers the caller wrote. It does
not teach meditation, time sessions, or judge practice.

Not claimed: that the days are accurate, that a streak reflects benefit, that it predicts
anything, or anything about health or the real world. Every claim flag in the result is
False.
"""
MAX_DAYS = 365
MAX_DAY = 100000
_TOP = frozenset({"days"})

NOT_CLAIMED = (
    "the days are accurate",
    "a streak reflects benefit",
    "the tallies predict anything",
    "health or real-world outcome",
)
CLAIMS = {"accurate_days": False, "benefit": False, "predictive": False, "health_claim": False}


class StreakError(ValueError):
    pass


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise StreakError("data keys must be exactly days")
    raw = data["days"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_DAYS:
        raise StreakError("days must be a list of 1..365 ints")
    prev = None
    for v in raw:
        if type(v) is not int:
            raise StreakError("days must be ints")
        if v < 0 or v > MAX_DAY:
            raise StreakError("day out of range")
        if prev is not None and v <= prev:
            raise StreakError("days must be strictly increasing")
        prev = v
    return list(raw)


def session_streaks(data):
    days = _validate(data)
    streaks = []
    cur = 1
    gap = 0
    for a, b in zip(days, days[1:]):
        if b == a + 1:
            cur += 1
        else:
            streaks.append(cur)
            cur = 1
            gap = max(gap, b - a - 1)
    streaks.append(cur)
    return {
        "status": "completed",
        "sessions": len(days),
        "streaks": len(streaks),
        "longest_streak": max(streaks),
        "current_streak": cur,
        "longest_gap": gap,
        "span": days[-1] - days[0] + 1,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
