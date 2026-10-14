"""Direct Instruction - exact time split of a caller-recorded lesson into explain, model, practice and check.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
segments, 1..8 lesson segments in order, each [phase, minutes]: phase one of the strings
explain, model, practice, check and minutes an int 1..60. The data key is exactly segments.

The result gives "minutes", a dict of phase -> total minutes for each phase present (in the
order explain, model, practice, check); "total" minutes; "shares", a dict of phase -> its
minutes divided by total as an exact Fraction string (same order); "missing", the phases
absent from the lesson (in that same order); and "in_order": true when no segment's phase
comes earlier in the order explain, model, practice, check than the segment before it.

Scope: PARTIAL for the Direct Instruction line. Counting minutes in a segment list the caller
wrote. It does not teach or judge a lesson.

Not claimed: that the lesson took place, that this split is the right one, that the order is
required for learning, or anything about the real world. Every claim flag in the result is
False.
"""
from fractions import Fraction

PHASES = ("explain", "model", "practice", "check")
NOT_CLAIMED = (
    "the lesson took place",
    "this split is the right one",
    "the order is required for learning",
    "real-world outcome",
)
CLAIMS = {"took_place": False, "right_split": False, "order_required": False, "real_world": False}


class LessonError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"segments"}:
        raise LessonError("data keys must be exactly segments")
    v = data["segments"]
    if type(v) is not list or not 1 <= len(v) <= 8:
        raise LessonError("segments must be a list of 1 to 8 segments")
    out = []
    for e in v:
        if type(e) is not list or len(e) != 2:
            raise LessonError("each segment must be a list of [phase, minutes]")
        p, m = e
        if type(p) is not str or p not in PHASES:
            raise LessonError("phase must be one of explain, model, practice, check")
        if type(m) is not int:
            raise LessonError("minutes must be an int")
        if not 1 <= m <= 60:
            raise LessonError("minutes must be 1 to 60")
        out.append((p, m))
    return out


def lesson_phases(data):
    seg = _validate(data)
    tot = {}
    for p, m in seg:
        tot[p] = tot.get(p, 0) + m
    total = sum(tot.values())
    present = [p for p in PHASES if p in tot]
    ranks = [PHASES.index(p) for p, _ in seg]
    return {
        "status": "completed",
        "minutes": {p: tot[p] for p in present},
        "total": total,
        "shares": {p: str(Fraction(tot[p], total)) for p in present},
        "missing": [p for p in PHASES if p not in tot],
        "in_order": all(ranks[i] >= ranks[i - 1] for i in range(1, len(ranks))),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
