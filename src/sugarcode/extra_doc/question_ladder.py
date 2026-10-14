"""Inquiry-Based Learning - exact depth and answer summary of a caller-recorded list of student questions.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
questions, 1..10 questions in the order asked, each [depth, answered]: depth an int 1..4
(1 recall, 2 explain, 3 apply, 4 evaluate, as the caller labelled them) and answered the int
1 or 0. The data key is exactly questions.

The result gives "by_depth", a list of 4 counts (index 0 is depth 1); "mean_depth" as an
exact Fraction string; "answered_share" as an exact Fraction string; "deepest_answered", the
largest depth among answered questions (null when none answered); and "deepening": true when
no question is shallower than the one before it (depths never fall).

Scope: bounded for the Inquiry-Based Learning line. Counting over labels the caller wrote. It
does not judge the questions or run an inquiry.

Not claimed: that the depth labels are right, that deeper questions mean better learning, that
answers were correct, or anything about the real world. Every claim flag in the result is False.
"""
from fractions import Fraction

NOT_CLAIMED = (
    "the depth labels are right",
    "deeper questions mean better learning",
    "the answers were correct",
    "real-world outcome",
)
CLAIMS = {"labels_right": False, "deeper_is_better": False, "answers_correct": False, "real_world": False}


class LadderError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"questions"}:
        raise LadderError("data keys must be exactly questions")
    v = data["questions"]
    if type(v) is not list or not 1 <= len(v) <= 10:
        raise LadderError("questions must be a list of 1 to 10 questions")
    out = []
    for e in v:
        if type(e) is not list or len(e) != 2:
            raise LadderError("each question must be a list of [depth, answered]")
        dp, an = e
        if type(dp) is not int or type(an) is not int:
            raise LadderError("depth and answered must be ints")
        if not 1 <= dp <= 4:
            raise LadderError("depth must be 1 to 4")
        if an not in (0, 1):
            raise LadderError("answered must be 0 or 1")
        out.append((dp, an))
    return out


def question_ladder(data):
    q = _validate(data)
    by = [0, 0, 0, 0]
    for dp, _ in q:
        by[dp - 1] += 1
    answered = [dp for dp, an in q if an == 1]
    return {
        "status": "completed",
        "by_depth": by,
        "mean_depth": str(Fraction(sum(dp for dp, _ in q), len(q))),
        "answered_share": str(Fraction(len(answered), len(q))),
        "deepest_answered": max(answered) if answered else None,
        "deepening": all(q[i][0] >= q[i - 1][0] for i in range(1, len(q))),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
