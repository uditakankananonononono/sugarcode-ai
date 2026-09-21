"""Position weight matrices and log-odds motif scoring."""
from __future__ import annotations
import math

BASES = "ACGT"


def build_pwm(aligned_seqs: list[str], pseudocount: float = 0.5) -> list[dict[str, float]]:
    """Frequency PWM from aligned sequences (equal length)."""
    if not aligned_seqs:
        raise ValueError("no sequences")
    n = len(aligned_seqs[0])
    if any(len(s) != n for s in aligned_seqs):
        raise ValueError("sequences must be aligned to equal length")
    pwm = []
    for i in range(n):
        counts = {b: pseudocount for b in BASES}
        for s in aligned_seqs:
            b = s[i].upper()
            if b in counts:
                counts[b] += 1.0
        total = sum(counts.values())
        pwm.append({b: counts[b] / total for b in BASES})
    return pwm


def log_odds_matrix(pwm: list[dict[str, float]], background: float = 0.25) -> list[dict[str, float]]:
    return [{b: math.log2(max(p[b], 1e-9) / background) for b in BASES} for p in pwm]


def score(seq: str, lod: list[dict[str, float]]) -> float:
    """Log-odds score of a sequence against a log-odds matrix."""
    if len(seq) != len(lod):
        raise ValueError("sequence length must equal PWM length")
    return sum(lod[i].get(seq[i].upper(), -10.0) for i in range(len(lod)))


def max_score(lod: list[dict[str, float]]) -> float:
    return sum(max(col.values()) for col in lod)


def min_score(lod: list[dict[str, float]]) -> float:
    return sum(min(col.values()) for col in lod)


def normalized_score(seq: str, lod: list[dict[str, float]]) -> float:
    """0..1 score between worst and best possible binding."""
    lo, hi = min_score(lod), max_score(lod)
    if hi <= lo:
        return 0.0
    return (score(seq, lod) - lo) / (hi - lo)


def scan(seq: str, lod: list[dict[str, float]], threshold: float = 0.0) -> list[dict]:
    """Sliding-window scan; returns hits at/above normalized threshold."""
    k = len(lod)
    s = seq.upper()
    hits = []
    for i in range(len(s) - k + 1):
        ns = normalized_score(s[i:i + k], lod)
        if ns >= threshold:
            hits.append({"position": i, "sequence": s[i:i + k], "score": round(ns, 4)})
    return hits
