"""Vicarious Learning - exact tally of rewards and punishments a caller says an observer saw others receive.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
seen, 1..12 things the observer watched, each [action, outcome]: action a name (1..12
characters a-z and _), outcome the string reward or punish. The data key is exactly seen.

For each action the result gives rewards, punishes and net (rewards minus punishes), in a dict
keyed by action (keys sorted). It also lists "approach" (actions with net above 0), "avoid"
(net below 0) and "neutral" (net exactly 0), each sorted.

Scope: PARTIAL for the Vicarious Learning line. Counting over a list the caller wrote. It does
not watch anyone or say what the observer took from what they saw.

Not claimed: that the observer saw these outcomes, that net means the observer's choice,
that rewards and punishments weigh the same, or anything about the real world. Every claim flag
in the result is False.
"""
import re

_NAME = re.compile(r"[a-z_]{1,12}\Z")
NOT_CLAIMED = (
    "the observer saw these outcomes",
    "net decides the observer's choice",
    "rewards and punishments weigh the same",
    "real-world outcome",
)
CLAIMS = {"observer_saw": False, "decides_choice": False, "equal_weight": False, "real_world": False}


class VicariousError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"seen"}:
        raise VicariousError("data keys must be exactly seen")
    v = data["seen"]
    if type(v) is not list or not 1 <= len(v) <= 12:
        raise VicariousError("seen must be a list of 1 to 12 observations")
    out = []
    for e in v:
        if type(e) is not list or len(e) != 2:
            raise VicariousError("each observation must be a list of [action, outcome]")
        a, o = e
        if type(a) is not str or not _NAME.match(a):
            raise VicariousError("action must be 1..12 characters from a-z and _")
        if type(o) is not str or o not in ("reward", "punish"):
            raise VicariousError("outcome must be reward or punish")
        out.append((a, o))
    return out


def vicarious_tally(data):
    seen = _validate(data)
    t = {}
    for a, o in seen:
        r, p = t.get(a, (0, 0))
        t[a] = (r + 1, p) if o == "reward" else (r, p + 1)
    acts = sorted(t)
    return {
        "status": "completed",
        "actions": {a: {"rewards": t[a][0], "punishes": t[a][1], "net": t[a][0] - t[a][1]} for a in acts},
        "approach": [a for a in acts if t[a][0] > t[a][1]],
        "avoid": [a for a in acts if t[a][0] < t[a][1]],
        "neutral": [a for a in acts if t[a][0] == t[a][1]],
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
