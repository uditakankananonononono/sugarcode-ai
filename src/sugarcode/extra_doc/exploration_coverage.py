"""Discovery Learning - exact coverage of a small set of items by a caller-recorded exploration path.

Pure function over caller data. No network, no clock, no floats, no randomness. Input: items,
an int 2..10 (how many things there are to find, numbered 0 up to items - 1); visits, 1..16
ints in the order visited, each 0..items - 1. The data keys are exactly items, visits.

The result gives "first_visit", a list with one entry per item: the 0-based index in visits of
its first visit (null when never visited); "distinct", the number of different items visited;
"coverage", distinct divided by items as an exact Fraction string; "revisits", the number of
visits to an item already visited; "longest_new_run", the longest run of consecutive visits
that were each a first visit; and "unvisited", the sorted item numbers never visited.

Scope: PARTIAL for the Discovery Learning line. Counting over a path the caller wrote. It does
not run an exploration or judge what was found.

Not claimed: that the path happened, that coverage means discovery, that revisits are wasted,
or anything about the real world. Every claim flag in the result is False.
"""
from fractions import Fraction

NOT_CLAIMED = (
    "the path happened",
    "coverage means discovery",
    "revisits are wasted",
    "real-world outcome",
)
CLAIMS = {"happened": False, "coverage_is_discovery": False, "revisits_wasted": False, "real_world": False}


class ExplorationError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"items", "visits"}:
        raise ExplorationError("data keys must be exactly items, visits")
    n = data["items"]
    if type(n) is not int:
        raise ExplorationError("items must be an int")
    if not 2 <= n <= 10:
        raise ExplorationError("items must be 2 to 10")
    v = data["visits"]
    if type(v) is not list or not 1 <= len(v) <= 16:
        raise ExplorationError("visits must be a list of 1 to 16 visits")
    for x in v:
        if type(x) is not int:
            raise ExplorationError("visit must be an int")
        if not 0 <= x < n:
            raise ExplorationError("visit must be 0 to items - 1")
    return n, list(v)


def exploration_coverage(data):
    n, v = _validate(data)
    first = [None] * n
    new_flags = []
    for i, x in enumerate(v):
        if first[x] is None:
            first[x] = i
            new_flags.append(True)
        else:
            new_flags.append(False)
    best = run = 0
    for f in new_flags:
        run = run + 1 if f else 0
        if run > best:
            best = run
    distinct = sum(1 for f in first if f is not None)
    return {
        "status": "completed",
        "first_visit": first,
        "distinct": distinct,
        "coverage": str(Fraction(distinct, n)),
        "revisits": len(v) - distinct,
        "longest_new_run": best,
        "unvisited": [i for i in range(n) if first[i] is None],
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
