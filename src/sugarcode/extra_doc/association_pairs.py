"""Learning by Association - exact co-occurrence tally of stimulus pairs a caller presented together.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
pairs, 1..12 presentations, each a list of two different stimulus names (1..12 characters
a-z and _). Order inside a presentation does not matter: [a, b] and [b, a] are the same
pair. The data key is exactly pairs.

The result gives "counts", a list of [low, high, count] rows (names in alphabetical order
inside a row, rows sorted by low then high), "strongest", the row with the largest count
(ties go to the first row in that sorted order), "strongest_share", that count divided by the
number of presentations as an exact Fraction string, and "partners", a dict of stimulus ->
number of distinct stimuli it was paired with (keys sorted).

Scope: PARTIAL for the Learning by Association line. Counting over a presentation list the
caller wrote. It does not condition anyone or tell what was learned.

Not claimed: that the presentations happened, that frequent pairing means an association was
learned, that order is irrelevant for real learners, or anything about the real world. Every
claim flag in the result is False.
"""
import re
from fractions import Fraction

_NAME = re.compile(r"[a-z_]{1,12}\Z")
NOT_CLAIMED = (
    "the presentations happened",
    "frequent pairing means an association was learned",
    "order is irrelevant for real learners",
    "real-world outcome",
)
CLAIMS = {"happened": False, "association_learned": False, "order_irrelevant": False, "real_world": False}


class AssociationError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"pairs"}:
        raise AssociationError("data keys must be exactly pairs")
    p = data["pairs"]
    if type(p) is not list or not 1 <= len(p) <= 12:
        raise AssociationError("pairs must be a list of 1 to 12 presentations")
    out = []
    for e in p:
        if type(e) is not list or len(e) != 2:
            raise AssociationError("each presentation must be a list of two stimuli")
        for s in e:
            if type(s) is not str or not _NAME.match(s):
                raise AssociationError("stimulus must be 1..12 characters from a-z and _")
        if e[0] == e[1]:
            raise AssociationError("a presentation needs two different stimuli")
        out.append((min(e), max(e)))
    return out


def association_pairs(data):
    pairs = _validate(data)
    tally = {}
    for pr in pairs:
        tally[pr] = tally.get(pr, 0) + 1
    rows = [[a, b, tally[(a, b)]] for a, b in sorted(tally)]
    best = rows[0]
    for r in rows:
        if r[2] > best[2]:
            best = r
    partners = {}
    for a, b in tally:
        partners.setdefault(a, set()).add(b)
        partners.setdefault(b, set()).add(a)
    return {
        "status": "completed",
        "counts": rows,
        "strongest": list(best),
        "strongest_share": str(Fraction(best[2], len(pairs))),
        "partners": {k: len(partners[k]) for k in sorted(partners)},
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
