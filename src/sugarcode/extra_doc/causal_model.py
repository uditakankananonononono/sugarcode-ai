"""Mental Model Construction - exact representation of a caller-described cause graph.

Pure function over caller data. No inference about the real world, no network, no clock,
no floats, no randomness. Input: concepts, 1..12 distinct names (1..12 characters a-z and
_); links, 0..40 [cause, effect] pairs of known, distinct concepts, no duplicates.

The result builds the model: for each concept (alphabetical) its direct effects, direct
causes and every concept it can reach (its downstream set); the roots (no causes); the
leaves (no effects); whether the graph has a cycle; and, when there is none, the
topological order that always takes the alphabetically first available concept.

Scope: bounded implementation for the Mental Model Construction line. Graph bookkeeping on a model the
caller wrote. It builds no model from observations and checks nothing against the world.

Not claimed: that the links are true, that the model is complete, that the order is the
only valid one, or anything about the real world. Every claim flag in the result is False.
"""
import re

MAX_CONCEPTS = 12
MAX_LINKS = 40
_NAME = re.compile(r"[a-z_]{1,12}\Z")
_TOP = frozenset({"concepts", "links"})

NOT_CLAIMED = (
    "the links are true",
    "the model is complete",
    "the order is the only valid one",
    "real-world outcome",
)
CLAIMS = {"links_true": False, "complete": False, "unique_order": False, "real_world": False}


class ModelError(ValueError):
    pass


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise ModelError("data keys must be exactly concepts, links")
    cs = data["concepts"]
    if not isinstance(cs, list) or not 1 <= len(cs) <= MAX_CONCEPTS:
        raise ModelError("concepts must be a list of 1..12 names")
    for c in cs:
        if not type(c) is str or not _NAME.match(c):
            raise ModelError("concept must be 1..12 characters from a-z and _")
    if len(set(cs)) != len(cs):
        raise ModelError("concepts must be distinct")
    ls = data["links"]
    if not isinstance(ls, list) or len(ls) > MAX_LINKS:
        raise ModelError("links must be a list of at most 40 [cause, effect] pairs")
    known, seen, out = set(cs), set(), []
    for p in ls:
        if not isinstance(p, list) or len(p) != 2:
            raise ModelError("link must be a [cause, effect] pair")
        a, b = p
        if not type(a) is str or not type(b) is str or a not in known or b not in known:
            raise ModelError("link must use known concepts")
        if a == b:
            raise ModelError("link must join two different concepts")
        if (a, b) in seen:
            raise ModelError("links must be distinct")
        seen.add((a, b))
        out.append((a, b))
    return sorted(cs), out


def causal_model(data):
    cs, links = _validate(data)
    eff = {c: sorted(b for a, b in links if a == c) for c in cs}
    cau = {c: sorted(a for a, b in links if b == c) for c in cs}
    reach = {}
    for c in cs:
        seen, stack = set(), list(eff[c])
        while stack:
            x = stack.pop()
            if x not in seen:
                seen.add(x)
                stack.extend(eff[x])
        reach[c] = sorted(seen)
    indeg = {c: len(cau[c]) for c in cs}
    order = []
    avail = sorted(c for c in cs if indeg[c] == 0)
    while avail:
        c = avail.pop(0)
        order.append(c)
        for e in eff[c]:
            indeg[e] -= 1
            if indeg[e] == 0:
                avail.append(e)
        avail.sort()
    cyclic = len(order) != len(cs)
    return {
        "status": "completed",
        "model": {c: {"effects": eff[c], "causes": cau[c], "downstream": reach[c]} for c in cs},
        "roots": [c for c in cs if not cau[c]],
        "leaves": [c for c in cs if not eff[c]],
        "has_cycle": cyclic,
        "order": None if cyclic else order,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
