"""Set/count similarity metrics and bulk nearest-neighbour search."""
from __future__ import annotations

import heapq
from collections.abc import Iterable, Mapping

from .morgan import morgan_bits, morgan_counts


def tanimoto(a, b) -> float:
    """Tanimoto (= Jaccard). Sets of on-bits: |a&b| / |a|b|. Count dicts:
    sum min / (sum a + sum b - sum min), as RDKit TanimotoSimilarity on
    sparse int vectors. Two empty fingerprints give 0.0 (RDKit convention)."""
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        inter = sum(min(v, b[k]) for k, v in a.items() if k in b)
        denom = sum(a.values()) + sum(b.values()) - inter
    else:
        a, b = set(a), set(b)
        inter = len(a & b)
        denom = len(a) + len(b) - inter
    return inter / denom if denom else 0.0


jaccard = tanimoto


def dice(a, b) -> float:
    """Dice: 2|a&b| / (|a|+|b|); counts use sum min (RDKit DiceSimilarity)."""
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        inter = sum(min(v, b[k]) for k, v in a.items() if k in b)
        denom = sum(a.values()) + sum(b.values())
    else:
        a, b = set(a), set(b)
        inter = len(a & b)
        denom = len(a) + len(b)
    return 2 * inter / denom if denom else 0.0


def fingerprint(smiles: str, kind: str = "bits", radius: int = 2, n_bits: int = 2048):
    if kind == "bits":
        return morgan_bits(smiles, radius, n_bits)
    if kind == "counts":
        return morgan_counts(smiles, radius)
    raise ValueError("kind must be 'bits' or 'counts'")


def nearest_neighbors(query: str, library: Iterable[str], k: int = 5, kind: str = "bits",
                      radius: int = 2, n_bits: int = 2048, metric: str = "tanimoto",
                      threshold: float = 0.0, skip_invalid: bool = True) -> dict:
    """Rank a SMILES library by similarity to ``query``. Returns the top ``k``
    (ties broken by library order) at or above ``threshold``, plus any SMILES
    that failed to parse."""
    sim = {"tanimoto": tanimoto, "dice": dice}[metric]
    q = fingerprint(query, kind, radius, n_bits)
    scored, invalid = [], []
    for idx, smi in enumerate(library):
        try:
            fp = fingerprint(smi, kind, radius, n_bits)
        except ValueError as e:
            if not skip_invalid:
                raise
            invalid.append({"index": idx, "smiles": smi, "error": str(e)})
            continue
        s = sim(q, fp)
        if s >= threshold:
            scored.append((-s, idx, smi))
    top = heapq.nsmallest(k, scored)
    return {"query": query, "metric": metric, "fingerprint": f"morgan{kind} r={radius}" +
            (f" n_bits={n_bits}" if kind == "bits" else ""),
            "hits": [{"index": i, "smiles": s, "similarity": -ns} for ns, i, s in top],
            "invalid": invalid}


def similarity_matrix(smiles: list[str], kind: str = "bits", radius: int = 2,
                      n_bits: int = 2048, metric: str = "tanimoto") -> list[list[float]]:
    sim = {"tanimoto": tanimoto, "dice": dice}[metric]
    fps = [fingerprint(s, kind, radius, n_bits) for s in smiles]
    return [[sim(a, b) for b in fps] for a in fps]
