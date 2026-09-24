"""Pairwise sequence alignment: Needleman-Wunsch (global) and
Smith-Waterman (local) with Gotoh affine gaps, DNA match/mismatch or
vendored BLOSUM62 (data/alignment/blosum62.json, Henikoff & Henikoff 1992,
see PROVENANCE.md).

Gap-cost convention (matches Biopython's PairwiseAligner so the oracle
tests are exact): a gap of length L costs gap_open + (L-1) x gap_extend.
Pure-Python O(n x m) time and memory - intended for gene/protein-scale
inputs, not genomes.

Traceback tie-breaking is deterministic: diagonal (match state) preferred,
then extension of an existing gap, then opening the other gap.
"""
from __future__ import annotations

import json
from importlib import resources

_BLOSUM62 = None


def load_blosum62() -> dict:
    global _BLOSUM62
    if _BLOSUM62 is None:
        with resources.files("sugarcode.bio.data.alignment").joinpath(
                "blosum62.json").open() as fh:
            _BLOSUM62 = json.load(fh)["scores"]
    return _BLOSUM62


def _align(a: str, b: str, mode: str, match: float, mismatch: float,
           gap_open: float, gap_extend: float,
           matrix: dict | None) -> dict:
    a, b = a.upper(), b.upper()
    if not a or not b:
        raise ValueError("both sequences must be non-empty")
    if matrix is not None:
        for s in (set(a) | set(b)):
            if s not in matrix:
                raise ValueError(f"letter {s!r} not in the substitution "
                                 f"matrix")
    else:
        bad = sorted((set(a) | set(b)) - set("ACGT"))
        if bad:
            raise ValueError(f"invalid DNA letters {bad} - pass a matrix "
                             f"for non-ACGT alphabets")

    def sub(x, y):
        return matrix[x][y] if matrix is not None \
            else (match if x == y else mismatch)

    n, m = len(a), len(b)
    NEG = float("-inf")
    local = mode == "local"
    # M: a[i-1] aligned to b[j-1]; X: a[i-1] vs gap; Y: gap vs b[j-1]
    M = [[NEG] * (m + 1) for _ in range(n + 1)]
    X = [[NEG] * (m + 1) for _ in range(n + 1)]
    Y = [[NEG] * (m + 1) for _ in range(n + 1)]
    M[0][0] = 0.0
    for i in range(1, n + 1):
        X[i][0] = gap_open + (i - 1) * gap_extend
        if local:
            M[i][0] = 0.0
    for j in range(1, m + 1):
        Y[0][j] = gap_open + (j - 1) * gap_extend
        if local:
            M[0][j] = 0.0
    floor = 0.0 if local else NEG
    best, best_pos = (NEG if not local else 0.0), (0, 0)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            X[i][j] = max(M[i - 1][j] + gap_open, Y[i - 1][j] + gap_open,
                          X[i - 1][j] + gap_extend, floor)
            Y[i][j] = max(M[i][j - 1] + gap_open, X[i][j - 1] + gap_open,
                          Y[i][j - 1] + gap_extend, floor)
            M[i][j] = max(M[i - 1][j - 1], X[i - 1][j - 1],
                          Y[i - 1][j - 1], floor) + sub(a[i - 1], b[j - 1])
            if local and max(M[i][j], X[i][j], Y[i][j]) > best:
                best = max(M[i][j], X[i][j], Y[i][j])
                best_pos = (i, j)
    if local:
        i, j = best_pos
        total = best
    else:
        i, j = n, m
        total = max(M[n][m], X[n][m], Y[n][m])

    # traceback
    ali_a: list[str] = []
    ali_b: list[str] = []
    if local:
        state = max((("M", M[i][j]), ("X", X[i][j]), ("Y", Y[i][j])),
                    key=lambda kv: kv[1])[0]
    else:
        state = max((("M", M[n][m]), ("X", X[n][m]), ("Y", Y[n][m])),
                    key=lambda kv: kv[1])[0]
    while i > 0 or j > 0:
        if local and max(M[i][j] if i and j else NEG,
                         X[i][j], Y[i][j]) <= 0:
            break
        if state == "M":
            prev = [(M[i - 1][j - 1], "M"), (X[i - 1][j - 1], "X"),
                    (Y[i - 1][j - 1], "Y")]
            if local:
                prev.append((0.0, "STOP"))
            v, state = max(prev, key=lambda kv: kv[0])
            ali_a.append(a[i - 1])
            ali_b.append(b[j - 1])
            i, j = i - 1, j - 1
            if state == "STOP":
                break
        elif state == "X":
            # prefer extending an open gap, then M, then Y
            opts = [(X[i - 1][j] + gap_extend, "X"),
                    (M[i - 1][j] + gap_open, "M"),
                    (Y[i - 1][j] + gap_open, "Y")]
            cur = X[i][j]
            for v, s in opts:
                if v == cur:
                    state = s
                    break
            ali_a.append(a[i - 1])
            ali_b.append("-")
            i -= 1
        else:
            opts = [(Y[i][j - 1] + gap_extend, "Y"),
                    (M[i][j - 1] + gap_open, "M"),
                    (X[i][j - 1] + gap_open, "X")]
            cur = Y[i][j]
            for v, s in opts:
                if v == cur:
                    state = s
                    break
            ali_a.append("-")
            ali_b.append(b[j - 1])
            j -= 1
    aa, bb = "".join(reversed(ali_a)), "".join(reversed(ali_b))
    matches = sum(1 for x, y in zip(aa, bb) if x == y and x != "-")
    gaps = sum(1 for x, y in zip(aa, bb) if x == "-" or y == "-")
    return {"mode": mode, "score": round(total, 6), "aligned_a": aa,
            "aligned_b": bb, "length": len(aa), "matches": matches,
            "mismatches": len(aa) - matches - gaps, "gap_positions": gaps,
            "identity": round(matches / len(aa), 6) if aa else 0.0}


def nw_align(a: str, b: str, *, match: float = 2.0, mismatch: float = -1.0,
             gap_open: float = -5.0, gap_extend: float = -1.0,
             matrix: str | None = None) -> dict:
    """Needleman-Wunsch global alignment. matrix="BLOSUM62" selects the
    vendored protein matrix (match/mismatch ignored)."""
    m = load_blosum62() if matrix == "BLOSUM62" else None
    if matrix is not None and m is None:
        raise ValueError(f"unknown matrix {matrix!r}")
    return _align(a, b, "global", match, mismatch, gap_open, gap_extend, m)


def sw_align(a: str, b: str, *, match: float = 2.0, mismatch: float = -1.0,
             gap_open: float = -5.0, gap_extend: float = -1.0,
             matrix: str | None = None) -> dict:
    """Smith-Waterman local alignment."""
    m = load_blosum62() if matrix == "BLOSUM62" else None
    if matrix is not None and m is None:
        raise ValueError(f"unknown matrix {matrix!r}")
    return _align(a, b, "local", match, mismatch, gap_open, gap_extend, m)
