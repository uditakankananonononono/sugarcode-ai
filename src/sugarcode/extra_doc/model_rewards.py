"""Observational Learning - exact reward averages seen on a model and how often an observer chose the best-looking action.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
observed, 1..12 things seen the model do, each [action, reward]: action a name (1..12
characters a-z and _), reward an int -10..10; choices, 1..8 action names the observer then
chose. The data keys are exactly choices, observed.

The result gives "means", a dict of action -> mean observed reward as an exact Fraction
string (keys sorted); "best", the action with the largest mean (ties go to the
alphabetically first); "followed", how many of the observer's choices equal best; and
"follow_rate", followed divided by the number of choices as an exact Fraction string.

Scope: PARTIAL for the Observational Learning line. Averaging and counting over lists the
caller wrote. It does not watch anyone or tell why the observer chose as they did.

Not claimed: that the observed rewards were seen by the observer, that choosing the best
action shows learning from the model, that the rewards are comparable, or anything about
the real world. Every claim flag in the result is False.
"""
import re
from fractions import Fraction

_NAME = re.compile(r"[a-z_]{1,12}\Z")
NOT_CLAIMED = (
    "the observer saw the rewards",
    "choosing the best action shows learning from the model",
    "the rewards are comparable",
    "real-world outcome",
)
CLAIMS = {"observer_saw": False, "learned_from_model": False, "comparable_rewards": False, "real_world": False}


class ModelError(ValueError):
    pass


def _name(s):
    if type(s) is not str or not _NAME.match(s):
        raise ModelError("action must be 1..12 characters from a-z and _")
    return s


def _validate(data):
    if type(data) is not dict or set(data) != {"observed", "choices"}:
        raise ModelError("data keys must be exactly choices, observed")
    ob = data["observed"]
    if type(ob) is not list or not 1 <= len(ob) <= 12:
        raise ModelError("observed must be a list of 1 to 12 observations")
    seen = []
    for e in ob:
        if type(e) is not list or len(e) != 2:
            raise ModelError("each observation must be a list of [action, reward]")
        a = _name(e[0])
        r = e[1]
        if type(r) is not int:
            raise ModelError("reward must be an int")
        if not -10 <= r <= 10:
            raise ModelError("reward must be -10 to 10")
        seen.append((a, r))
    ch = data["choices"]
    if type(ch) is not list or not 1 <= len(ch) <= 8:
        raise ModelError("choices must be a list of 1 to 8 action names")
    return seen, [_name(c) for c in ch]


def model_rewards(data):
    seen, choices = _validate(data)
    tot = {}
    for a, r in seen:
        n, t = tot.get(a, (0, 0))
        tot[a] = (n + 1, t + r)
    means = {a: Fraction(tot[a][1], tot[a][0]) for a in sorted(tot)}
    best = None
    for a in means:
        if best is None or means[a] > means[best]:
            best = a
    followed = sum(1 for c in choices if c == best)
    return {
        "status": "completed",
        "means": {a: str(m) for a, m in means.items()},
        "best": best,
        "followed": followed,
        "follow_rate": str(Fraction(followed, len(choices))),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
