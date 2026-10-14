"""Reflective Practice - exact spacing and length summary of a caller-recorded reflection journal.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
entries, 1..12 journal entries in time order, each [day, words]: day an int 0..365 (strictly
larger than the previous entry's day) and words an int 0..500 (length of the entry). The data
key is exactly entries.

The result gives "count"; "total_words"; "mean_words" as an exact Fraction string; "gaps", the
days between neighbouring entries (later day minus earlier day); "longest_gap" (null with a
single entry); and "regular": true when there are at least 2 gaps and all gaps are equal.

Scope: bounded for the Reflective Practice line. Arithmetic on a journal summary the caller
wrote. It does not read the entries or judge the quality of anyone's reflection.

Not claimed: that the entries exist, that more words means deeper reflection, that regular
spacing means a habit, or anything about the real world. Every claim flag in the result is
False.
"""
from fractions import Fraction

NOT_CLAIMED = (
    "the entries exist",
    "more words means deeper reflection",
    "regular spacing means a habit",
    "real-world outcome",
)
CLAIMS = {"entries_exist": False, "words_are_depth": False, "spacing_is_habit": False, "real_world": False}


class ReflectionError(ValueError):
    pass


def _validate(data):
    if type(data) is not dict or set(data) != {"entries"}:
        raise ReflectionError("data keys must be exactly entries")
    v = data["entries"]
    if type(v) is not list or not 1 <= len(v) <= 12:
        raise ReflectionError("entries must be a list of 1 to 12 entries")
    out = []
    for e in v:
        if type(e) is not list or len(e) != 2:
            raise ReflectionError("each entry must be a list of [day, words]")
        d, w = e
        if type(d) is not int or type(w) is not int:
            raise ReflectionError("day and words must be ints")
        if not 0 <= d <= 365:
            raise ReflectionError("day must be 0 to 365")
        if not 0 <= w <= 500:
            raise ReflectionError("words must be 0 to 500")
        if out and d <= out[-1][0]:
            raise ReflectionError("days must be strictly increasing")
        out.append((d, w))
    return out


def reflection_gaps(data):
    ent = _validate(data)
    gaps = [ent[i + 1][0] - ent[i][0] for i in range(len(ent) - 1)]
    total = sum(w for _, w in ent)
    return {
        "status": "completed",
        "count": len(ent),
        "total_words": total,
        "mean_words": str(Fraction(total, len(ent))),
        "gaps": gaps,
        "longest_gap": max(gaps) if gaps else None,
        "regular": len(gaps) >= 2 and all(g == gaps[0] for g in gaps),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
