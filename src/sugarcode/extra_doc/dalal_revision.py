"""Belief Revision - exact Dalal revision of a small propositional belief base by new information.

Pure function over caller data. No network, no clock, no floats, no randomness. Input:
atoms, 1..5 distinct names (1..12 characters a-z and _); base and info, each 1..8 clauses,
a clause being 1..4 literals, a literal an atom name or "!" plus an atom name. A clause is
true when at least one literal is true; a set of clauses is true when every clause is.

Models are the 0/1 assignments to the atoms that make a clause set true. Dalal revision:
if the base has models and info has models, the revised models are the info models whose
Hamming distance to the nearest base model is smallest. If the base has no models the
revised models are the info models. If info has no models the revision is refused
(inconsistent new information).

The result gives the number of base models, the number of info models, the revised models
as strings over the atoms in alphabetical order (sorted), the distance used (0 when the
base has no models), and the literals true in every revised model.

Scope: PARTIAL for the Belief Revision line. One concrete revision operator, brute force
over at most 32 assignments. It is not a theory of belief change and picks no operator for
anyone else.

Not claimed: that the base reflects anyone's beliefs, that Dalal is the right operator,
that the revised base is true, or anything about the real world. Every claim flag in the
result is False.
"""
import itertools
import re

_NAME = re.compile(r"[a-z_]{1,12}\Z")
_TOP = frozenset({"atoms", "base", "info"})

NOT_CLAIMED = (
    "the base reflects anyone's beliefs",
    "Dalal is the right operator",
    "the revised base is true",
    "real-world outcome",
)
CLAIMS = {"real_beliefs": False, "right_operator": False, "revised_true": False, "real_world": False}


class RevisionError(ValueError):
    pass


def _clauses(raw, atoms, what):
    if not isinstance(raw, list) or not 1 <= len(raw) <= 8:
        raise RevisionError(f"{what} must be a list of 1..8 clauses")
    out = []
    for c in raw:
        if not isinstance(c, list) or not 1 <= len(c) <= 4:
            raise RevisionError(f"each clause in {what} must be a list of 1..4 literals")
        lits = []
        for lit in c:
            if not type(lit) is str:
                raise RevisionError("literal must be a string")
            neg = lit.startswith("!")
            name = lit[1:] if neg else lit
            if name not in atoms:
                raise RevisionError("literal must use a known atom")
            lits.append((name, not neg))
        out.append(lits)
    return out


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise RevisionError("data keys must be exactly atoms, base, info")
    at = data["atoms"]
    if not isinstance(at, list) or not 1 <= len(at) <= 5:
        raise RevisionError("atoms must be a list of 1..5 names")
    for a in at:
        if not type(a) is str or not _NAME.match(a):
            raise RevisionError("atom must be 1..12 characters from a-z and _")
    if len(set(at)) != len(at):
        raise RevisionError("atoms must be distinct")
    known = set(at)
    return sorted(at), _clauses(data["base"], known, "base"), _clauses(data["info"], known, "info")


def _models(atoms, clauses):
    out = []
    for bits in itertools.product((0, 1), repeat=len(atoms)):
        val = dict(zip(atoms, bits))
        if all(any(bool(val[n]) == pos for n, pos in c) for c in clauses):
            out.append(bits)
    return out


def dalal_revision(data):
    atoms, base, info = _validate(data)
    bm, im = _models(atoms, base), _models(atoms, info)
    if not im:
        raise RevisionError("new information is inconsistent")
    if bm:
        dist = {m: min(sum(x != y for x, y in zip(m, b)) for b in bm) for m in im}
        best = min(dist.values())
        rev = [m for m in im if dist[m] == best]
    else:
        best, rev = 0, im
    lits = []
    for i, a in enumerate(atoms):
        col = {m[i] for m in rev}
        if col == {1}:
            lits.append(a)
        elif col == {0}:
            lits.append("!" + a)
    return {
        "status": "completed",
        "base_models": len(bm),
        "info_models": len(im),
        "revised": ["".join(map(str, m)) for m in rev],
        "distance": best,
        "entailed": lits,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
