"""Guided Discovery - exact hint use across a caller-recorded run of guided attempts.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
attempts, 1..10 attempts in order, each [hints, correct]: hints an int 0..5 (how many hints
the learner was given) and correct the int 1 or 0. The data key is exactly attempts.

The result gives "total_hints"; "unaided_correct", the number of attempts that were correct
with 0 hints; "correct"; "unaided_share", unaided_correct divided by correct as an exact
Fraction string (null when nothing was correct); "first_correct", the 0-based index of the
first correct attempt (null when none); and "fading": true when no attempt used more hints
than the attempt before it.

Scope: PARTIAL for the Guided Discovery line. Counting over a list the caller wrote. It does not
guide anyone or judge the hints.

Not claimed: that the hints were good, that fewer hints means learning, that correct flags
were judged soundly, or anything about the real world. Every claim flag in the result is False.
"""
from fractions import Fraction

NOT_CLAIMED = (
    "the hints were good",
    "fewer hints means learning",
    "the correct flags were judged soundly",
    "real-world outcome",
)
CLAIMS = {"good_hints": False, "fewer_is_learning": False, "sound_judgement": False, "real_world": False}


class HintError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"attempts"}:
        raise HintError("data keys must be exactly attempts")
    v = data["attempts"]
    if type(v) is not list or not 1 <= len(v) <= 10:
        raise HintError("attempts must be a list of 1 to 10 attempts")
    out = []
    for e in v:
        if type(e) is not list or len(e) != 2:
            raise HintError("each attempt must be a list of [hints, correct]")
        h, c = e
        if type(h) is not int or type(c) is not int:
            raise HintError("hints and correct must be ints")
        if not 0 <= h <= 5:
            raise HintError("hints must be 0 to 5")
        if c not in (0, 1):
            raise HintError("correct must be 0 or 1")
        out.append((h, c))
    return out


def hint_fading(data):
    a = _validate(data)
    correct = sum(c for _, c in a)
    unaided = sum(1 for h, c in a if c == 1 and h == 0)
    first = None
    for i, (_, c) in enumerate(a):
        if c == 1:
            first = i
            break
    return {
        "status": "completed",
        "total_hints": sum(h for h, _ in a),
        "correct": correct,
        "unaided_correct": unaided,
        "unaided_share": str(Fraction(unaided, correct)) if correct else None,
        "first_correct": first,
        "fading": all(a[i][0] <= a[i - 1][0] for i in range(1, len(a))),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
