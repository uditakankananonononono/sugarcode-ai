"""Social Learning - exact one-round adoption spread over a small caller-described network.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
state, 2..8 ints, each 1 (has adopted the behaviour) or 0 (has not), one per person
numbered from 0; ties, 0..16 pairs [i, j] of different person numbers (ints 0 up to
len(state) - 1), each pair listed once in either order. The data keys are exactly state,
ties.

One round, all people updated at the same time from the old state: a person who has adopted
keeps it; a person who has not adopts when strictly more than half of their ties have
adopted (2 * adopted_ties > ties). The result gives "state", the new 0/1 list; "adopted_now",
the sorted person numbers who adopted this round; "adopters", the count of 1s afterwards; and
"share", adopters divided by the number of people as an exact Fraction string.

Scope: bounded implementation for the Social Learning line. One fixed adoption rule applied once to a
network the caller wrote. It does not model real people or tell what they learn from each other.

Not claimed: that people copy a majority, that ties are real, that one round shows spread over
time, or anything about the real world. Every claim flag in the result is False.
"""
from fractions import Fraction

NOT_CLAIMED = (
    "people copy a majority",
    "the ties are real",
    "one round shows spread over time",
    "real-world outcome",
)
CLAIMS = {"copy_majority": False, "real_ties": False, "spread_over_time": False, "real_world": False}


class AdoptionError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"state", "ties"}:
        raise AdoptionError("data keys must be exactly state, ties")
    s = data["state"]
    if type(s) is not list or not 2 <= len(s) <= 8:
        raise AdoptionError("state must be a list of 2 to 8 values")
    for x in s:
        if type(x) is not int:
            raise AdoptionError("state value must be an int")
        if x not in (0, 1):
            raise AdoptionError("state value must be 0 or 1")
    t = data["ties"]
    if type(t) is not list or len(t) > 16:
        raise AdoptionError("ties must be a list of at most 16 ties")
    seen = set()
    for e in t:
        if type(e) is not list or len(e) != 2:
            raise AdoptionError("each tie must be a list of two person numbers")
        for p in e:
            if type(p) is not int:
                raise AdoptionError("person number must be an int")
            if not 0 <= p < len(s):
                raise AdoptionError("person number must be between 0 and len(state) - 1")
        if e[0] == e[1]:
            raise AdoptionError("a tie needs two different people")
        key = (min(e), max(e))
        if key in seen:
            raise AdoptionError("ties must not repeat")
        seen.add(key)
    return list(s), sorted(seen)


def peer_adoption(data):
    s, ties = _validate(data)
    deg = [0] * len(s)
    on = [0] * len(s)
    for a, b in ties:
        deg[a] += 1
        deg[b] += 1
        on[a] += s[b]
        on[b] += s[a]
    new = [1 if s[i] == 1 or 2 * on[i] > deg[i] else 0 for i in range(len(s))]
    now = [i for i in range(len(s)) if s[i] == 0 and new[i] == 1]
    return {
        "status": "completed",
        "state": new,
        "adopted_now": now,
        "adopters": sum(new),
        "share": str(Fraction(sum(new), len(s))),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
