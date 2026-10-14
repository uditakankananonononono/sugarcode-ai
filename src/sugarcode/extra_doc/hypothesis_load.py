"""Problem-Based Learning - exact hypothesis counts per problem in a caller-recorded problem set.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
problems, 1..8 problems, each [name, hypotheses, resolved]: name a label (1..12 characters
a-z and _, all different), hypotheses an int 1..10 (how many explanations the group tried)
and resolved the int 1 or 0. The data key is exactly problems.

The result gives "hypotheses", a dict of name -> hypotheses (keys sorted); "resolved", the
sorted names with resolved 1; "unresolved", the sorted names with resolved 0; "total"; and
"mean_per_resolved", the mean hypotheses over resolved problems as an exact Fraction string
(null when none is resolved); "heaviest", the name with the most hypotheses (ties to the
alphabetically first).

Scope: bounded for the Problem-Based Learning line. Counting over a list the caller wrote. It
does not run a class or judge the problems.

Not claimed: that the problems were worked, that more hypotheses means better learning, that
resolved flags were judged soundly, or anything about the real world. Every claim flag in the
result is False.
"""
import re
from fractions import Fraction

_NAME = re.compile(r"[a-z_]{1,12}\Z")
NOT_CLAIMED = (
    "the problems were worked",
    "more hypotheses means better learning",
    "the resolved flags were judged soundly",
    "real-world outcome",
)
CLAIMS = {"worked": False, "more_is_better": False, "sound_judgement": False, "real_world": False}


class ProblemError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"problems"}:
        raise ProblemError("data keys must be exactly problems")
    v = data["problems"]
    if type(v) is not list or not 1 <= len(v) <= 8:
        raise ProblemError("problems must be a list of 1 to 8 problems")
    out = {}
    for e in v:
        if type(e) is not list or len(e) != 3:
            raise ProblemError("each problem must be a list of [name, hypotheses, resolved]")
        n, h, r = e
        if type(n) is not str or not _NAME.match(n):
            raise ProblemError("name must be 1..12 characters from a-z and _")
        if type(h) is not int or type(r) is not int:
            raise ProblemError("hypotheses and resolved must be ints")
        if not 1 <= h <= 10:
            raise ProblemError("hypotheses must be 1 to 10")
        if r not in (0, 1):
            raise ProblemError("resolved must be 0 or 1")
        if n in out:
            raise ProblemError("names must be distinct")
        out[n] = (h, r)
    return out


def hypothesis_load(data):
    p = _validate(data)
    names = sorted(p)
    res = [n for n in names if p[n][1] == 1]
    hyp = {n: p[n][0] for n in names}
    heavy = names[0]
    for n in names:
        if hyp[n] > hyp[heavy]:
            heavy = n
    return {
        "status": "completed",
        "hypotheses": hyp,
        "resolved": res,
        "unresolved": [n for n in names if p[n][1] == 0],
        "total": sum(hyp.values()),
        "mean_per_resolved": str(Fraction(sum(hyp[n] for n in res), len(res))) if res else None,
        "heaviest": heavy,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
