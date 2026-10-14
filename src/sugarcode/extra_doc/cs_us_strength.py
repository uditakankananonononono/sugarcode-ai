"""Classical Conditioning - exact Rescorla-Wagner strength of a conditioned stimulus over caller-given trials.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
trials, 1..12 ints, each 1 (the conditioned stimulus was followed by the unconditioned
stimulus) or 0 (it was not); rate, an int 1..100 (learning rate in percent). The data keys
are exactly rate, trials.

The strength starts at 0. On each trial strength becomes strength + rate/100 * (100 * trial
- strength), computed with exact Fractions. The result gives the strength after each trial as
a Fraction string ("strengths"), the final strength, and "trials_to_half": the 1-based number
of the first trial after which the strength is at least 50 (null when it never is).

Scope: bounded implementation for the Classical Conditioning line. One textbook update rule applied to a
trial list the caller wrote. It does not condition anyone or estimate a real learning rate.

Not claimed: that real learners follow this rule, that the rate fits anyone, that strength
predicts a response, or anything about the real world. Every claim flag in the result is
False.
"""
from fractions import Fraction

NOT_CLAIMED = (
    "real learners follow this rule",
    "the rate fits anyone",
    "strength predicts a response",
    "real-world outcome",
)
CLAIMS = {"real_learners": False, "rate_fits": False, "predicts_response": False, "real_world": False}


class ConditioningError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"trials", "rate"}:
        raise ConditioningError("data keys must be exactly rate, trials")
    t = data["trials"]
    if type(t) is not list or not 1 <= len(t) <= 12:
        raise ConditioningError("trials must be a list of 1 to 12 trials")
    for x in t:
        if type(x) is not int:
            raise ConditioningError("trial must be an int")
        if x not in (0, 1):
            raise ConditioningError("trial must be 0 or 1")
    r = data["rate"]
    if type(r) is not int:
        raise ConditioningError("rate must be an int")
    if not 1 <= r <= 100:
        raise ConditioningError("rate must be 1 to 100")
    return list(t), r


def cs_us_strength(data):
    trials, rate = _validate(data)
    v = Fraction(0)
    out = []
    for x in trials:
        v = v + Fraction(rate, 100) * (100 * x - v)
        out.append(v)
    half = None
    for i, s in enumerate(out):
        if s >= 50:
            half = i + 1
            break
    return {
        "status": "completed",
        "strengths": [str(s) for s in out],
        "final": str(out[-1]),
        "trials_to_half": half,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
