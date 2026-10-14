"""Formal Learning - exact credit-weighted grade average of a caller-recorded set of courses.

Pure function over caller data. No network, no clock, no floats, no randomness. Input: courses,
1..8 courses, each [name, credits, points]: name a label (1..12 characters a-z and _, all
different), credits an int 1..6 and points an int 0..4 (grade points earned). The data key is
exactly courses.

The result gives "total_credits"; "earned_credits", the credits of courses with points above 0;
"average", the sum of credits times points over total credits as an exact Fraction string;
"failed", the sorted names with 0 points; and "heaviest", the name with the most credits (ties
go to the alphabetically first).

Scope: PARTIAL for the Formal Learning line. Credit-weighted arithmetic on grades the caller
wrote. It does not assess anyone or say what a course taught.

Not claimed: that the grades are real, that the average measures learning, that 0 points means
a fail at any real institution, or anything about the real world. Every claim flag in the
result is False.
"""
import re
from fractions import Fraction

_NAME = re.compile(r"[a-z_]{1,12}\Z")
NOT_CLAIMED = (
    "the grades are real",
    "the average measures learning",
    "0 points means a fail at any real institution",
    "real-world outcome",
)
CLAIMS = {"real_grades": False, "measures_learning": False, "zero_is_fail": False, "real_world": False}


class GradeError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"courses"}:
        raise GradeError("data keys must be exactly courses")
    v = data["courses"]
    if type(v) is not list or not 1 <= len(v) <= 8:
        raise GradeError("courses must be a list of 1 to 8 courses")
    out = {}
    for e in v:
        if type(e) is not list or len(e) != 3:
            raise GradeError("each course must be a list of [name, credits, points]")
        n, c, p = e
        if type(n) is not str or not _NAME.match(n):
            raise GradeError("name must be 1..12 characters from a-z and _")
        if type(c) is not int or type(p) is not int:
            raise GradeError("credits and points must be ints")
        if not 1 <= c <= 6:
            raise GradeError("credits must be 1 to 6")
        if not 0 <= p <= 4:
            raise GradeError("points must be 0 to 4")
        if n in out:
            raise GradeError("names must be distinct")
        out[n] = (c, p)
    return out


def course_grades(data):
    c = _validate(data)
    names = sorted(c)
    total = sum(c[n][0] for n in names)
    heavy = names[0]
    for n in names:
        if c[n][0] > c[heavy][0]:
            heavy = n
    return {
        "status": "completed",
        "total_credits": total,
        "earned_credits": sum(c[n][0] for n in names if c[n][1] > 0),
        "average": str(Fraction(sum(c[n][0] * c[n][1] for n in names), total)),
        "failed": [n for n in names if c[n][1] == 0],
        "heaviest": heavy,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
