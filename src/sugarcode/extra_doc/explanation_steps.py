"""Explicit Instruction - exact completeness check of a caller-described step-by-step explanation.

Pure function over caller data. No network, no clock, no floats, no randomness. Input: steps,
1..10 explained steps, each [name, examples, checked]: name a label (1..12 characters a-z
and _, all different), examples an int 0..5 (worked examples given for the step) and checked
the int 1 or 0 (the explainer checked understanding after the step). The data key is exactly
steps.

The result gives "total_examples"; "without_example", the sorted names with 0 examples;
"unchecked", the sorted names with checked 0; "checked_share", checked steps over all steps
as an exact Fraction string; and "complete": true when no step is without an example and no
step is unchecked.

Scope: bounded for the Explicit Instruction line. Counting over a list the caller wrote. It does
not teach or judge an explanation.

Not claimed: that the explanation was clear, that examples or checks caused understanding, that
the flags were recorded soundly, or anything about the real world. Every claim flag in the
result is False.
"""
import re
from fractions import Fraction

_NAME = re.compile(r"[a-z_]{1,12}\Z")
NOT_CLAIMED = (
    "the explanation was clear",
    "examples or checks caused understanding",
    "the flags were recorded soundly",
    "real-world outcome",
)
CLAIMS = {"clear": False, "caused_understanding": False, "sound_flags": False, "real_world": False}


class ExplanationError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"steps"}:
        raise ExplanationError("data keys must be exactly steps")
    v = data["steps"]
    if type(v) is not list or not 1 <= len(v) <= 10:
        raise ExplanationError("steps must be a list of 1 to 10 steps")
    out = {}
    for e in v:
        if type(e) is not list or len(e) != 3:
            raise ExplanationError("each step must be a list of [name, examples, checked]")
        n, x, c = e
        if type(n) is not str or not _NAME.match(n):
            raise ExplanationError("name must be 1..12 characters from a-z and _")
        if type(x) is not int or type(c) is not int:
            raise ExplanationError("examples and checked must be ints")
        if not 0 <= x <= 5:
            raise ExplanationError("examples must be 0 to 5")
        if c not in (0, 1):
            raise ExplanationError("checked must be 0 or 1")
        if n in out:
            raise ExplanationError("names must be distinct")
        out[n] = (x, c)
    return out


def explanation_steps(data):
    s = _validate(data)
    names = sorted(s)
    none = [n for n in names if s[n][0] == 0]
    unchecked = [n for n in names if s[n][1] == 0]
    return {
        "status": "completed",
        "total_examples": sum(s[n][0] for n in names),
        "without_example": none,
        "unchecked": unchecked,
        "checked_share": str(Fraction(len(names) - len(unchecked), len(names))),
        "complete": not none and not unchecked,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
