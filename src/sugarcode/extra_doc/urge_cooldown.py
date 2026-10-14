"""Impulse Control - exact check of a caller-supplied waiting rule against logged urge-to-action gaps.

Pure function over caller data. No clock, no sensors, no floats, no randomness. Input:
events, 1..200 [urge_minute, action_minute] int pairs with 0 <= urge <= action <=
1000000; cooldown, an int 1..100000 (the minimum minutes the rule asks to wait).

An event follows the rule when action - urge >= cooldown. The result gives, per event,
the wait and whether it followed the rule; the number that followed it; the share that
followed it as an exact Fraction string; the shortest wait; and the longest wait.

Scope: PARTIAL for the Impulse Control line. Arithmetic on gaps the caller logged. It does
not detect urges, enforce anything, or judge behaviour.

Not claimed: that the times are accurate, that waiting helps, that a followed rule shows
control, or anything about health or the real world. Every claim flag in the result is
False.
"""
from fractions import Fraction

MAX_EVENTS = 200
MAX_MINUTE = 1000000
MAX_COOLDOWN = 100000
_TOP = frozenset({"events", "cooldown"})

NOT_CLAIMED = (
    "the times are accurate",
    "waiting helps",
    "a followed rule shows control",
    "health or real-world outcome",
)
CLAIMS = {"accurate_times": False, "waiting_helps": False, "shows_control": False, "health_claim": False}


class CooldownError(ValueError):
    pass


def _int(v, lo, hi, name):
    if type(v) is not int:
        raise CooldownError(f"{name} must be an int")
    if v < lo or v > hi:
        raise CooldownError(f"{name} out of range")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise CooldownError("data keys must be exactly cooldown, events")
    raw = data["events"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_EVENTS:
        raise CooldownError("events must be a list of 1..200 [urge, action] pairs")
    ev = []
    for p in raw:
        if not isinstance(p, list) or len(p) != 2:
            raise CooldownError("event must be an [urge, action] pair")
        u = _int(p[0], 0, MAX_MINUTE, "urge")
        a = _int(p[1], 0, MAX_MINUTE, "action")
        if a < u:
            raise CooldownError("action must not be before urge")
        ev.append((u, a))
    return ev, _int(data["cooldown"], 1, MAX_COOLDOWN, "cooldown")


def urge_cooldown(data):
    ev, cd = _validate(data)
    rows = [{"wait": a - u, "followed": a - u >= cd} for u, a in ev]
    waits = [r["wait"] for r in rows]
    n_ok = sum(1 for r in rows if r["followed"])
    return {
        "status": "completed",
        "events": rows,
        "followed": n_ok,
        "followed_share": str(Fraction(n_ok, len(rows))),
        "shortest_wait": min(waits),
        "longest_wait": max(waits),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
