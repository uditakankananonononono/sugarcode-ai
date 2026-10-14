"""Learning by Insight - exact detection of a sudden jump in a caller-recorded progress series.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
series, 3..12 ints 0..100 (progress after each step); threshold, an int 1..100. The data
keys are exactly series, threshold.

The result gives the change at each step (each value minus the one before); "jump", the
largest change; "jump_at", the 0-based index in series of the first value reaching that
largest change; "plateau", the number of steps before jump_at whose change is 0; and
"sudden": true when jump is at least threshold and every other change is at most half
of it (exact test: 2 * other <= jump).

Scope: bounded implementation for the Learning by Insight line. Arithmetic on a progress series the
caller wrote. It does not observe anyone's understanding or say what caused a jump.

Not claimed: that the series measures understanding, that a sudden jump is insight, that
the steps are comparable, or anything about the real world. Every claim flag in the result
is False.
"""

NOT_CLAIMED = (
    "the series measures understanding",
    "a sudden jump is insight",
    "the steps are comparable",
    "real-world outcome",
)
CLAIMS = {"measures_understanding": False, "jump_is_insight": False, "comparable_steps": False, "real_world": False}


class InsightError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"series", "threshold"}:
        raise InsightError("data keys must be exactly series, threshold")
    s = data["series"]
    if type(s) is not list or not 3 <= len(s) <= 12:
        raise InsightError("series must be a list of 3 to 12 values")
    for x in s:
        if type(x) is not int:
            raise InsightError("series values must be ints")
        if not 0 <= x <= 100:
            raise InsightError("series values must be 0 to 100")
    t = data["threshold"]
    if type(t) is not int:
        raise InsightError("threshold must be an int")
    if not 1 <= t <= 100:
        raise InsightError("threshold must be 1 to 100")
    return list(s), t


def insight_jump(data):
    s, t = _validate(data)
    ch = [s[i] - s[i - 1] for i in range(1, len(s))]
    jump = max(ch)
    k = ch.index(jump)
    plateau = sum(1 for c in ch[:k] if c == 0)
    others = ch[:k] + ch[k + 1:]
    sudden = jump >= t and all(2 * c <= jump for c in others)
    return {
        "status": "completed",
        "changes": ch,
        "jump": jump,
        "jump_at": k + 1,
        "plateau": plateau,
        "sudden": sudden,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
