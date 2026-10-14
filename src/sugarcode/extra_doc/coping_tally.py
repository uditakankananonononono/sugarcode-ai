"""Coping Strategies - exact per-strategy success tally from caller-supplied attempts.

Pure function over caller data. No clock, no sensors, no floats, no randomness. Input:
attempts, 1..300 [strategy, worked] pairs; strategy is 1..12 characters from a-z and _
(at most 10 distinct), worked is 1 (the caller says it helped) or 0.

For each strategy (alphabetical) the result gives attempts, worked, and the share that
worked as an exact Fraction string. "top" is the strategy with the highest share among
those with at least 2 attempts; ties go to the strategy with more attempts, then to the
alphabetically first. "top" is null when no strategy has 2 attempts.

Scope: PARTIAL for the Coping Strategies line. Counting on attempts the caller logged. It
does not recommend strategies or assess coping.

Not claimed: that the log is accurate, that a strategy caused help, that "top" is the best
strategy for the person, or anything about health or the real world. Every claim flag in
the result is False.
"""
import re
from fractions import Fraction

MAX_ATTEMPTS = 300
MAX_STRATEGIES = 10
MIN_FOR_TOP = 2
_NAME = re.compile(r"[a-z_]{1,12}\Z")
_TOP = frozenset({"attempts"})

NOT_CLAIMED = (
    "the log is accurate",
    "a strategy caused help",
    "top is the best strategy for the person",
    "health or real-world outcome",
)
CLAIMS = {"accurate_log": False, "causal": False, "best_for_person": False, "health_claim": False}


class CopingError(ValueError):
    pass


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise CopingError("data keys must be exactly attempts")
    raw = data["attempts"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_ATTEMPTS:
        raise CopingError("attempts must be a list of 1..300 [strategy, worked] pairs")
    out = []
    for p in raw:
        if not isinstance(p, list) or len(p) != 2:
            raise CopingError("attempt must be a [strategy, worked] pair")
        s, w = p
        if not type(s) is str or not _NAME.match(s):
            raise CopingError("strategy must be 1..12 characters from a-z and _")
        if type(w) is not int:
            raise CopingError("worked must be an int")
        if w not in (0, 1):
            raise CopingError("worked must be 0 or 1")
        out.append((s, w))
    if len({s for s, _ in out}) > MAX_STRATEGIES:
        raise CopingError("at most 10 distinct strategies")
    return out


def coping_tally(data):
    att = _validate(data)
    tot, won = {}, {}
    for s, w in att:
        tot[s] = tot.get(s, 0) + 1
        won[s] = won.get(s, 0) + w
    rows = {s: {"attempts": tot[s], "worked": won[s], "share": str(Fraction(won[s], tot[s]))} for s in sorted(tot)}
    eligible = [s for s in sorted(tot) if tot[s] >= MIN_FOR_TOP]
    top = None
    for s in eligible:
        if top is None or (Fraction(won[s], tot[s]), tot[s]) > (Fraction(won[top], tot[top]), tot[top]):
            top = s
    return {
        "status": "completed",
        "strategies": rows,
        "top": top,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
