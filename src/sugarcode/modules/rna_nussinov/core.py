"""Nussinov-Jacobson maximum base-pair RNA secondary structure.

Nussinov R, Jacobson AB. "Fast algorithm for predicting the secondary structure
of single-stranded RNA." Proc Natl Acad Sci USA 1980;77(11):6309-6313,
DOI 10.1073/pnas.77.11.6309, PMID 6161375, PMC350273.

This is the pure combinatorial algorithm: it maximises the number of allowed
base pairs in a nested (pseudoknot-free) structure. It has no energy model and
no external parameter tables, so it is NOT a thermodynamic (MFE) predictor;
real folds are driven by stacking energies, which this does not model.

Recurrence (unambiguous: every structure is built exactly one way, by the fate
of the first base of the interval), over half-open intervals [i, j):

    N[i, j] = max( N[i+1, j],                                  # i unpaired
                   max_k 1 + N[i+1, k] + N[k+1, j] )           # i pairs k

where k ranges over i + min_loop + 1 <= k < j with (s[i], s[k]) an allowed pair.
Because the decomposition is unambiguous, the same tables also count the
number of distinct optimal structures exactly (``optimal_structure_count``).

Traceback tie-break (deterministic): leave i unpaired if that is optimal,
otherwise pair i with the smallest optimal partner k.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

WATSON_CRICK = frozenset({("A", "U"), ("U", "A"), ("G", "C"), ("C", "G")})
WOBBLE = frozenset({("G", "U"), ("U", "G")})
MAX_LENGTH = 2000
BRUTE_FORCE_MAX_LENGTH = 20
REFERENCE = {
    "algorithm": "Nussinov-Jacobson maximum base-pair dynamic programming",
    "publication": "Nussinov R, Jacobson AB. Proc Natl Acad Sci USA 1980;77(11):6309-6313",
    "doi": "10.1073/pnas.77.11.6309",
    "pmid": "6161375",
    "pmcid": "PMC350273",
    "limit": "maximises pair count only; no energy model, no pseudoknots",
}


def normalize_sequence(sequence: str) -> str:
    """Uppercase, strip whitespace, T -> U. Raises on any other symbol."""
    seq = "".join(str(sequence).split()).upper().replace("T", "U")
    bad = sorted(set(seq) - set("ACGU"))
    if bad:
        raise ValueError(f"unsupported nucleotide symbol(s) {bad}; only A, C, G, U (T accepted as U)")
    return seq


def allowed_pairs(allow_gu: bool = True) -> frozenset:
    return WATSON_CRICK | WOBBLE if allow_gu else WATSON_CRICK


def _check_params(n: int, min_loop: int, max_length: int) -> None:
    if not isinstance(min_loop, int) or min_loop < 0:
        raise ValueError("min_loop must be a non-negative integer")
    if n > max_length:
        raise ValueError(f"sequence length {n} exceeds max_length {max_length} (O(n^3) algorithm)")


@dataclass
class _Tables:
    seq: str
    min_loop: int
    N: np.ndarray                     # N[i, j] for half-open [i, j), shape (n+1, n+1)
    partners: list                    # partners[i] = sorted np.array of k pairable with i
    counts: list | None = field(default=None)


def _fill(seq: str, min_loop: int, allow_gu: bool) -> _Tables:
    n = len(seq)
    ok = allowed_pairs(allow_gu)
    partners = [np.array([k for k in range(i + min_loop + 1, n) if (seq[i], seq[k]) in ok], dtype=np.int64)
                for i in range(n)]
    N = np.zeros((n + 1, n + 1), dtype=np.int64)
    for i in range(n - 1, -1, -1):
        ks_all = partners[i]
        row_next = N[i + 1]
        for j in range(i + 1, n + 1):
            best = row_next[j]
            if ks_all.size:
                ks = ks_all[: np.searchsorted(ks_all, j)]
                if ks.size:
                    cand = 1 + row_next[ks] + N[ks + 1, j]
                    m = cand.max()
                    if m > best:
                        best = m
            N[i, j] = best
    return _Tables(seq, min_loop, N, partners)


def _optimal_ks(t: _Tables, i: int, j: int) -> list[int]:
    ks = t.partners[i][: np.searchsorted(t.partners[i], j)]
    if not ks.size:
        return []
    cand = 1 + t.N[i + 1, ks] + t.N[ks + 1, j]
    return [int(k) for k in ks[cand == t.N[i, j]]]


def _count(t: _Tables) -> int:
    """Exact number of distinct optimal structures (Python big ints)."""
    n = len(t.seq)
    C = [[1] * (n + 1) for _ in range(n + 2)]      # empty / unpairable intervals: 1 structure
    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n + 1):
            total = C[i + 1][j] if t.N[i + 1, j] == t.N[i, j] else 0
            for k in _optimal_ks(t, i, j):
                total += C[i + 1][k] * C[k + 1][j]
            C[i][j] = total
    t.counts = C
    return C[0][n] if n else 1


def _traceback(t: _Tables) -> list[tuple[int, int]]:
    pairs, stack = [], [(0, len(t.seq))]
    while stack:
        i, j = stack.pop()
        if j - i < 2:
            continue
        if t.N[i + 1, j] == t.N[i, j]:
            stack.append((i + 1, j))
            continue
        k = _optimal_ks(t, i, j)[0]
        pairs.append((i, k))
        stack.append((k + 1, j))
        stack.append((i + 1, k))
    return sorted(pairs)


def pairs_to_dot_bracket(pairs, n: int) -> str:
    s = ["."] * n
    for i, j in pairs:
        s[i], s[j] = "(", ")"
    return "".join(s)


def dot_bracket_to_pairs(structure: str) -> list[tuple[int, int]]:
    """Parse a nested dot-bracket string ('(', ')', '.') into 0-based pairs."""
    stack, pairs = [], []
    for idx, ch in enumerate(structure):
        if ch == "(":
            stack.append(idx)
        elif ch == ")":
            if not stack:
                raise ValueError(f"unbalanced ')' at position {idx}")
            pairs.append((stack.pop(), idx))
        elif ch != ".":
            raise ValueError(f"unsupported dot-bracket symbol {ch!r} at position {idx}")
    if stack:
        raise ValueError(f"unbalanced '(' at position {stack[-1]}")
    return sorted(pairs)


def structure_stats(sequence: str, pairs) -> dict:
    """Pair-count statistics for a nested structure."""
    seq = normalize_sequence(sequence)
    n = len(seq)
    pairs = sorted((int(i), int(j)) for i, j in pairs)
    pair_set = set(pairs)
    kinds = {"GC": 0, "AU": 0, "GU": 0}
    for i, j in pairs:
        key = {"CG": "GC", "AU": "AU", "GU": "GU"}.get("".join(sorted(seq[i] + seq[j])), "non_canonical")
        kinds[key] = kinds.get(key, 0) + 1
    # stems = maximal runs of directly stacked pairs (i, j), (i+1, j-1)
    stems = [p for p in pairs if (p[0] - 1, p[1] + 1) not in pair_set]
    stem_lengths = []
    for i, j in stems:
        length = 1
        while (i + length, j - length) in pair_set:
            length += 1
        stem_lengths.append(length)
    # hairpins = pairs enclosing no other pair
    partner = {}
    for i, j in pairs:
        partner[i], partner[j] = j, i
    hairpins = sum(1 for i, j in pairs if all(x not in partner for x in range(i + 1, j)))
    depth = max_depth = 0
    for ch in pairs_to_dot_bracket(pairs, n):
        depth += ch == "("
        depth -= ch == ")"
        max_depth = max(max_depth, depth)
    return {"length": n, "pair_count": len(pairs), "paired_bases": 2 * len(pairs),
            "unpaired_bases": n - 2 * len(pairs),
            "paired_fraction": (2 * len(pairs) / n) if n else 0.0,
            "pair_types": kinds, "stem_count": len(stems), "stem_lengths": stem_lengths,
            "hairpin_count": hairpins, "max_nesting_depth": max_depth}


def evaluate_structure(sequence: str, structure: str, *, min_loop: int = 3, allow_gu: bool = True) -> dict:
    """Check a dot-bracket structure against the model's rules; return stats and violations."""
    seq = normalize_sequence(sequence)
    if len(structure) != len(seq):
        raise ValueError("structure length must equal sequence length")
    pairs = dot_bracket_to_pairs(structure)
    ok = allowed_pairs(allow_gu)
    violations = []
    for i, j in pairs:
        if (seq[i], seq[j]) not in ok:
            violations.append({"pair": [i, j], "reason": f"{seq[i]}-{seq[j]} is not an allowed pair"})
        if j - i - 1 < min_loop:
            violations.append({"pair": [i, j], "reason": f"loop of {j - i - 1} < min_loop {min_loop}"})
    return {"valid": not violations, "violations": violations, "pairs": pairs,
            **structure_stats(seq, pairs)}


def fold(sequence: str, *, min_loop: int = 3, allow_gu: bool = True,
         count_optimal: bool | None = None, max_length: int = MAX_LENGTH) -> dict:
    """Maximum base-pair secondary structure with traceback.

    ``min_loop``: minimum unpaired bases enclosed by any pair (hairpin loop).
    ``allow_gu``: include G-U wobble pairs (default True).
    ``count_optimal``: count all distinct optimal structures (default: on for
    length <= 400). Returns dot-bracket, 0-based and 1-based pair lists, stats.
    """
    seq = normalize_sequence(sequence)
    n = len(seq)
    _check_params(n, min_loop, max_length)
    t = _fill(seq, min_loop, allow_gu)
    pairs = _traceback(t)
    if count_optimal is None:
        count_optimal = n <= 400
    result = {
        "sequence": seq,
        "dot_bracket": pairs_to_dot_bracket(pairs, n),
        "pairs": [list(p) for p in pairs],
        "pairs_1based": [[i + 1, j + 1] for i, j in pairs],
        "max_pairs": int(t.N[0, n]) if n else 0,
        "optimal_structure_count": _count(t) if count_optimal else None,
        "parameters": {"min_loop": min_loop, "allow_gu": allow_gu},
        "stats": structure_stats(seq, pairs),
        "reference": REFERENCE,
    }
    assert result["max_pairs"] == len(pairs)
    return result


def optimal_structures(sequence: str, *, min_loop: int = 3, allow_gu: bool = True,
                       limit: int = 1000, max_length: int = MAX_LENGTH) -> list[str]:
    """All distinct optimal structures (dot-bracket), up to ``limit``, sorted."""
    seq = normalize_sequence(sequence)
    n = len(seq)
    _check_params(n, min_loop, max_length)
    t = _fill(seq, min_loop, allow_gu)
    out: list[str] = []

    def expand(todo: list, pairs: list) -> bool:
        if len(out) >= limit:
            return False
        while todo and todo[-1][1] - todo[-1][0] < 2:
            todo = todo[:-1]
        if not todo:
            out.append(pairs_to_dot_bracket(pairs, n))
            return len(out) < limit
        i, j = todo[-1]
        rest = todo[:-1]
        if t.N[i + 1, j] == t.N[i, j]:
            if not expand(rest + [(i + 1, j)], pairs):
                return False
        for k in _optimal_ks(t, i, j):
            if not expand(rest + [(k + 1, j), (i + 1, k)], pairs + [(i, k)]):
                return False
        return True

    expand([(0, n)], [])
    return sorted(out)


def brute_force(sequence: str, *, min_loop: int = 3, allow_gu: bool = True) -> dict:
    """Independent exhaustive verifier for short sequences (n <= 20).

    Enumerates every set of allowed pairs that is pairwise compatible (no shared
    base, no crossing, loop >= min_loop) by plain backtracking over the list of
    candidate pairs - no dynamic programming, no shared code with ``fold``.
    """
    seq = normalize_sequence(sequence)
    n = len(seq)
    if n > BRUTE_FORCE_MAX_LENGTH:
        raise ValueError(f"brute force is limited to length {BRUTE_FORCE_MAX_LENGTH}")
    if not isinstance(min_loop, int) or min_loop < 0:
        raise ValueError("min_loop must be a non-negative integer")
    ok = allowed_pairs(allow_gu)
    cand = [(i, j) for i in range(n) for j in range(i + min_loop + 1, n) if (seq[i], seq[j]) in ok]
    best, best_structs, total = 0, [], 0

    def compatible(p, chosen):
        a, b = p
        for c, d in chosen:
            if a in (c, d) or b in (c, d):
                return False
            if a < c < b < d or c < a < d < b:
                return False
        return True

    def rec(idx, chosen):
        nonlocal best, best_structs, total
        if idx == len(cand):
            total += 1
            k = len(chosen)
            if k > best:
                best, best_structs = k, [list(chosen)]
            elif k == best:
                best_structs.append(list(chosen))
            return
        rec(idx + 1, chosen)
        if compatible(cand[idx], chosen):
            chosen.append(cand[idx])
            rec(idx + 1, chosen)
            chosen.pop()

    rec(0, [])
    return {"max_pairs": best, "optimal_structures": sorted(pairs_to_dot_bracket(s, n) for s in best_structs),
            "valid_structure_count": total}
