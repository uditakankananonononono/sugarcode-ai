"""Action Learning - exact tally of questions asked while a caller-recorded team worked on a problem.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
steps, 1..12 working steps in time order, each [questions, solved]: questions an int 0..20
(how many questions the team asked in the step) and solved the int 1 (the problem counted as
solved at the end of the step) or 0. The data key is exactly steps.

The result gives "total_questions"; "solved_steps", the number of steps with solved 1;
"first_solved", the 0-based index of the first such step (null when none);
"questions_before_solve", the questions asked in the steps before that one (null when none
solved); and "questions_per_solved_step" as an exact Fraction string (null when none solved).

Scope: PARTIAL for the Action Learning line. Counting over a step list the caller wrote. It does
not run a team or judge the questions.

Not claimed: that the steps happened, that asking more questions led to a solution, that
solved flags were judged soundly, or anything about the real world. Every claim flag in the
result is False.
"""
from fractions import Fraction

NOT_CLAIMED = (
    "the steps happened",
    "more questions led to a solution",
    "the solved flags were judged soundly",
    "real-world outcome",
)
CLAIMS = {"happened": False, "questions_led_to_solution": False, "sound_judgement": False, "real_world": False}


class StepsError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"steps"}:
        raise StepsError("data keys must be exactly steps")
    v = data["steps"]
    if type(v) is not list or not 1 <= len(v) <= 12:
        raise StepsError("steps must be a list of 1 to 12 steps")
    out = []
    for e in v:
        if type(e) is not list or len(e) != 2:
            raise StepsError("each step must be a list of [questions, solved]")
        q, s = e
        if type(q) is not int or type(s) is not int:
            raise StepsError("questions and solved must be ints")
        if not 0 <= q <= 20:
            raise StepsError("questions must be 0 to 20")
        if s not in (0, 1):
            raise StepsError("solved must be 0 or 1")
        out.append((q, s))
    return out


def question_steps(data):
    st = _validate(data)
    total = sum(q for q, _ in st)
    solved = sum(s for _, s in st)
    first = None
    for i, (_, s) in enumerate(st):
        if s == 1:
            first = i
            break
    return {
        "status": "completed",
        "total_questions": total,
        "solved_steps": solved,
        "first_solved": first,
        "questions_before_solve": None if first is None else sum(q for q, _ in st[:first]),
        "questions_per_solved_step": None if solved == 0 else str(Fraction(total, solved)),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
