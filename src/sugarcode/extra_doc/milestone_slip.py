"""Project-Based Learning - exact planned-versus-actual slip of a caller-recorded set of project milestones.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
milestones, 1..10 milestones, each [planned, done]: two ints 0..365, the day it was planned
for and the day it was finished. The data key is exactly milestones.

The slip of a milestone is done minus planned (negative means early). The result gives
"slips" in input order; "on_time", the number of milestones with slip 0 or below; "late", the
number with slip above 0; "on_time_share" as an exact Fraction string; "mean_slip" as an exact
Fraction string; and "worst", the 0-based index of the first milestone with the largest slip.

Scope: PARTIAL for the Project-Based Learning line. Arithmetic on milestone days the caller
wrote. It does not run a project or judge what students learned from it.

Not claimed: that the days are real, that being on time shows learning, that the milestones
are equally hard, or anything about the real world. Every claim flag in the result is False.
"""
from fractions import Fraction

NOT_CLAIMED = (
    "the days are real",
    "being on time shows learning",
    "the milestones are equally hard",
    "real-world outcome",
)
CLAIMS = {"real_days": False, "on_time_is_learning": False, "equal_difficulty": False, "real_world": False}


class MilestoneError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"milestones"}:
        raise MilestoneError("data keys must be exactly milestones")
    v = data["milestones"]
    if type(v) is not list or not 1 <= len(v) <= 10:
        raise MilestoneError("milestones must be a list of 1 to 10 milestones")
    out = []
    for e in v:
        if type(e) is not list or len(e) != 2:
            raise MilestoneError("each milestone must be a list of [planned, done]")
        for x in e:
            if type(x) is not int:
                raise MilestoneError("days must be ints")
            if not 0 <= x <= 365:
                raise MilestoneError("days must be 0 to 365")
        out.append((e[0], e[1]))
    return out


def milestone_slip(data):
    ms = _validate(data)
    slips = [done - planned for planned, done in ms]
    on_time = sum(1 for s in slips if s <= 0)
    worst = 0
    for i, s in enumerate(slips):
        if s > slips[worst]:
            worst = i
    return {
        "status": "completed",
        "slips": slips,
        "on_time": on_time,
        "late": len(slips) - on_time,
        "on_time_share": str(Fraction(on_time, len(slips))),
        "mean_slip": str(Fraction(sum(slips), len(slips))),
        "worst": worst,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
