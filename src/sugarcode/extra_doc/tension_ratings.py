"""Relaxation - exact before/after tension change per body region from caller-supplied ratings.

Pure function over caller data. No sensors, no clock, no floats, no randomness. Input:
regions, 1..10 dicts with exactly the keys name (1..12 characters a-z and _, unique),
before and after (ints 0..10, the caller's own tension ratings).

The result gives, per region in input order, the change (before - after, positive means
less tension); the total change; the total before; the total reduction as a share of the
total before as an exact Fraction string (null when the total before is 0); the number of
regions that improved, stayed equal and worsened; and the region with the largest change
(ties go to the earlier region in input order).

Scope: PARTIAL for the Relaxation line. Arithmetic on ratings the caller wrote. It does not
measure tension, teach relaxation, or advise.

Not claimed: that the ratings are accurate, that a relaxation method caused the change,
that the change lasts, or anything about health or the real world. Every claim flag in the
result is False.
"""
import re
from fractions import Fraction

MAX_REGIONS = 10
_NAME = re.compile(r"[a-z_]{1,12}\Z")
_REGION = frozenset({"name", "before", "after"})
_TOP = frozenset({"regions"})

NOT_CLAIMED = (
    "the ratings are accurate",
    "a relaxation method caused the change",
    "the change lasts",
    "health or real-world outcome",
)
CLAIMS = {"accurate_ratings": False, "causal": False, "lasting": False, "health_claim": False}


class TensionError(ValueError):
    pass


def _rating(v, name):
    if type(v) is not int:
        raise TensionError(f"{name} must be an int")
    if v < 0 or v > 10:
        raise TensionError(f"{name} out of range")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise TensionError("data keys must be exactly regions")
    raw = data["regions"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_REGIONS:
        raise TensionError("regions must be a list of 1..10 regions")
    out, seen = [], set()
    for r in raw:
        if not isinstance(r, dict) or set(r) != _REGION:
            raise TensionError("region keys must be exactly after, before, name")
        n = r["name"]
        if not type(n) is str or not _NAME.match(n):
            raise TensionError("name must be 1..12 characters from a-z and _")
        if n in seen:
            raise TensionError("region names must be unique")
        seen.add(n)
        out.append((n, _rating(r["before"], "before"), _rating(r["after"], "after")))
    return out


def tension_ratings(data):
    regs = _validate(data)
    rows = [{"name": n, "change": b - a} for n, b, a in regs]
    total_before = sum(b for _, b, _ in regs)
    total = sum(r["change"] for r in rows)
    best = rows[0]
    for r in rows[1:]:
        if r["change"] > best["change"]:
            best = r
    return {
        "status": "completed",
        "regions": rows,
        "total_change": total,
        "total_before": total_before,
        "share_reduced": str(Fraction(total, total_before)) if total_before else None,
        "improved": sum(1 for r in rows if r["change"] > 0),
        "equal": sum(1 for r in rows if r["change"] == 0),
        "worsened": sum(1 for r in rows if r["change"] < 0),
        "largest_change": best["name"],
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
