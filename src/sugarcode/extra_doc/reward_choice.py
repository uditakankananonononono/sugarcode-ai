"""Delayed Gratification - exact comparison of a smaller sooner reward with a larger later one.

Pure function over caller data. No clock, no floats, no randomness. Input: sooner, int
1..1000000 (the amount now); later, int 1..1000000 greater than sooner; delay, int
1..3650 (periods to wait); rate_num and rate_den, ints with 0 <= num <= 100 and
1 <= den <= 100 (a simple discount rate per period, num/den).

Rule (simple discounting): the later amount is worth later / (1 + rate * delay) now. The
choice is "later" when that value is above sooner, "sooner" when below, "tie" when equal.
The result also gives the value as an exact Fraction string and the break-even rate per
period, (later - sooner) / (sooner * delay), as an exact Fraction string.

Scope: PARTIAL for the Delayed Gratification line. Exact arithmetic for one stated
discounting rule. It does not measure anyone's patience or say which choice is wiser.

Not claimed: that the rate is the person's real rate, that the rule is how people decide,
that the rewards are comparable in real life, or anything about the real world. Every
claim flag in the result is False.
"""
from fractions import Fraction

_TOP = frozenset({"sooner", "later", "delay", "rate_num", "rate_den"})

NOT_CLAIMED = (
    "the rate is the person's real rate",
    "the rule is how people decide",
    "the rewards are comparable in real life",
    "real-world outcome",
)
CLAIMS = {"real_rate": False, "models_people": False, "comparable_rewards": False, "real_world": False}


class RewardError(ValueError):
    pass


def _int(data, key, lo, hi):
    v = data[key]
    if type(v) is not int:
        raise RewardError(f"{key} must be an int")
    if v < lo or v > hi:
        raise RewardError(f"{key} out of range")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise RewardError("data keys must be exactly delay, later, rate_den, rate_num, sooner")
    s = _int(data, "sooner", 1, 1000000)
    lt = _int(data, "later", 1, 1000000)
    if lt <= s:
        raise RewardError("later must be greater than sooner")
    d = _int(data, "delay", 1, 3650)
    num = _int(data, "rate_num", 0, 100)
    den = _int(data, "rate_den", 1, 100)
    return s, lt, d, num, den


def reward_choice(data):
    s, lt, d, num, den = _validate(data)
    value = Fraction(lt) / (1 + Fraction(num, den) * d)
    choice = "later" if value > s else "sooner" if value < s else "tie"
    return {
        "status": "completed",
        "choice": choice,
        "later_value_now": str(value),
        "break_even_rate": str(Fraction(lt - s, s * d)),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
