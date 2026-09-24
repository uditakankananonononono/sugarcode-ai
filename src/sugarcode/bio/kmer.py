"""k-mer toolkit: canonical counting, set operations, Jaccard/containment,
minimizer sketches.

PROVENANCE
- Canonical k-mers (strand-collapsed to the lexicographic minimum of a k-mer
  and its reverse complement): the convention used by Mash and standard de
  Bruijn assemblers (Ondov et al. 2016, below).
- Winnowing / minimizers: Roberts M, Hayes W, Hunt BR, Mount SM, Yorke JA
  (2004) "Reducing storage requirements for biological sequence comparison",
  Bioinformatics 20(18):3363-3369 - in each window of w consecutive k-mers
  keep the minimum; on ties keep the RIGHTMOST occurrence.
- MinHash sketching and the Mash distance: Ondov BD, Treangen TJ, Melsted P
  et al. (2016) "Mash: fast genome and metagenome distance estimation using
  MinHash", Genome Biology 17:132. mash_distance(j, k) = -ln(2j/(1+j)) / k.
- Sketch ordering hash: 64-bit FNV-1a (Fowler/Noll/Vo, public domain; offset
  basis 0xcbf29ce484222325, prime 0x100000001b3; reference test vectors
  published at http://www.isthe.com/chongo/tech/comp/fnv/ and verified in
  the test suite). Mash itself orders k-mers by MurmurHash3; this toolkit
  uses FNV-1a so it stays dependency-free and pinned to published test
  vectors. Any deterministic total order yields a valid minimizer scheme -
  the choice is stated here, not hidden.
- Jaccard / containment: standard set statistics behind MinHash theory
  (Broder 1997).

CONVENTIONS (documented next to every function)
- Sequences are uppercased; any window containing a non-ACGT base yields NO
  k-mer (the ambiguous base breaks the window instead of corrupting it).
- canonical=True (default) strand-collapses every k-mer; palindromic k-mers
  (possible at even k) collapse to themselves, no special casing.
- File inputs pool every record of a FASTA/FASTQ into ONE set/count
  (union semantics across records).
- An empty valid k-mer stream has jaccard(empty, empty) = 1.0 (identical),
  jaccard(empty, X) = 0.0, containment(empty, X) = 0.0.
- A sequence whose valid k-mer stream is shorter than w contributes its
  single global minimum as the sketch (Roberts et al. 2004).
"""
from __future__ import annotations

import math
from collections import deque
from pathlib import Path

from .sequence import reverse_complement

_MASK64 = (1 << 64) - 1
_FNV_OFFSET = 0xCBF29CE484222325
_FNV_PRIME = 0x100000001B3


def fnv1a64(text: str) -> int:
    """64-bit FNV-1a hash of a string (UTF-8). Public-domain algorithm;
    verified against the published FNV reference vectors in the tests."""
    h = _FNV_OFFSET
    for byte in text.encode("utf-8"):
        h ^= byte
        h = (h * _FNV_PRIME) & _MASK64
    return h


def canonical_kmer(kmer: str) -> str:
    """Strand-collapse a k-mer: the lexicographic minimum of the k-mer and
    its reverse complement."""
    kmer = kmer.upper()
    rc = reverse_complement(kmer)
    return kmer if kmer <= rc else rc


def iter_kmers(seq: str, k: int, canonical: bool = True):
    """Yield k-mers of an uppercased sequence, skipping any window that
    contains a non-ACGT base. canonical=True strand-collapses each k-mer."""
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")
    s = seq.upper()
    for i in range(len(s) - k + 1):
        window = s[i:i + k]
        if any(c not in "ACGT" for c in window):
            continue
        yield canonical_kmer(window) if canonical else window


def count_kmers(seq: str, k: int, canonical: bool = True) -> dict:
    """k-mer -> count over one sequence (empty dict when k > len(seq))."""
    counts: dict[str, int] = {}
    for kmer in iter_kmers(seq, k, canonical):
        counts[kmer] = counts.get(kmer, 0) + 1
    return counts


def kmer_set(seq: str, k: int, canonical: bool = True) -> set:
    """Distinct k-mers of one sequence."""
    return set(iter_kmers(seq, k, canonical))


def set_operations(a: set, b: set) -> dict:
    """Union / intersection / difference / symmetric difference of two sets."""
    return {
        "union": a | b,
        "intersection": a & b,
        "difference": a - b,
        "symmetric_difference": a ^ b,
    }


def jaccard(a: set, b: set) -> float:
    """|A n B| / |A u B|; jaccard(empty, empty) = 1.0 by convention."""
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def containment(a: set, b: set) -> float:
    """Fraction of A present in B: |A n B| / |A|; 0.0 when A is empty."""
    if not a:
        return 0.0
    return len(a & b) / len(a)


def compare_sequences(seq_a: str, seq_b: str, k: int,
                      canonical: bool = True) -> dict:
    """Exact k-mer similarity between two sequences."""
    a, b = kmer_set(seq_a, k, canonical), kmer_set(seq_b, k, canonical)
    shared = len(a & b)
    return {
        "mode": "exact", "k": k, "canonical": canonical,
        "size_a": len(a), "size_b": len(b), "shared": shared,
        "jaccard": jaccard(a, b),
        "containment_a_in_b": containment(a, b),
        "containment_b_in_a": containment(b, a),
    }


def load_sequences(path: str | Path) -> list[str]:
    """Read every record of a FASTA ('>') or FASTQ ('@') file, auto-detected
    on the first non-blank character. Returns the sequences only."""
    from .fasta import parse_fasta
    from .fastq import parse_fastq
    text = Path(path).read_text()
    first = next((c for c in text if not c.isspace()), "")
    if first == ">":
        return [r["sequence"] for r in parse_fasta(text)]
    if first == "@":
        return [r["sequence"] for r in parse_fastq(text)]
    raise ValueError(f"{path}: not FASTA or FASTQ (first char {first!r})")


def compare_files(path_a: str | Path, path_b: str | Path, k: int,
                  canonical: bool = True) -> dict:
    """Exact k-mer similarity between two files; each file pools all of its
    records into one k-mer set (union semantics)."""
    pooled = []
    for path in (path_a, path_b):
        s: set = set()
        for seq in load_sequences(path):
            s |= kmer_set(seq, k, canonical)
        pooled.append(s)
    a, b = pooled
    return {
        "mode": "exact", "k": k, "canonical": canonical,
        "file_a": str(path_a), "file_b": str(path_b),
        "size_a": len(a), "size_b": len(b), "shared": len(a & b),
        "jaccard": jaccard(a, b),
        "containment_a_in_b": containment(a, b),
        "containment_b_in_a": containment(b, a),
    }


def minimizers(seq: str, k: int, w: int, canonical: bool = True,
               order: str = "hash") -> list:
    """Minimizer sketch of one sequence: the sorted distinct minimizer
    k-mers from winnowing with window w (rightmost kept on ties;
    Roberts et al. 2004). order='hash' ranks k-mers by FNV-1a (Mash-style),
    order='lex' ranks them lexicographically (the original winnowing
    formulation). A valid k-mer stream shorter than w yields its single
    global minimum; an empty stream yields an empty sketch."""
    if w < 1:
        raise ValueError(f"w must be >= 1, got {w}")
    kmers = list(iter_kmers(seq, k, canonical))
    if not kmers:
        return []
    if order == "hash":
        keys = [fnv1a64(x) for x in kmers]
    elif order == "lex":
        keys = kmers
    else:
        raise ValueError(f"order must be 'hash' or 'lex', got {order!r}")
    if len(kmers) <= w:
        best = min(range(len(kmers)), key=lambda i: (keys[i], -i))
        return sorted({kmers[best]})
    dq: deque = deque()
    picked: list[int] = []
    for i in range(len(kmers)):
        while dq and keys[dq[-1]] >= keys[i]:  # >= keeps rightmost on ties
            dq.pop()
        dq.append(i)
        if dq[0] <= i - w:
            dq.popleft()
        if i >= w - 1:
            m = dq[0]
            if not picked or picked[-1] != m:
                picked.append(m)
    return sorted({kmers[i] for i in picked})


def mash_distance(j: float, k: int) -> float:
    """Mash distance from a Jaccard index (Ondov et al. 2016):
    -ln(2j/(1+j)) / k. j = 0 gives inf; j = 1 gives 0."""
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")
    if j <= 0.0:
        return math.inf
    if j >= 1.0:
        return 0.0
    return -math.log(2.0 * j / (1.0 + j)) / k


def compare_sketches(seq_a: str, seq_b: str, k: int, w: int,
                     canonical: bool = True, order: str = "hash") -> dict:
    """Minimizer-sketch similarity estimate (Mash-style). Reported values
    are ESTIMATES over the sketches, not exact set statistics; w = 1 makes
    the sketch the full k-mer set, so estimates equal the exact values."""
    a = set(minimizers(seq_a, k, w, canonical, order))
    b = set(minimizers(seq_b, k, w, canonical, order))
    j = jaccard(a, b)
    return {
        "mode": "minimizer-sketch", "k": k, "w": w, "order": order,
        "canonical": canonical,
        "sketch_a": len(a), "sketch_b": len(b), "shared": len(a & b),
        "jaccard_estimate": j,
        "containment_a_in_b_estimate": containment(a, b),
        "containment_b_in_a_estimate": containment(b, a),
        "mash_distance": mash_distance(j, k),
        "note": "sketch estimates, not exact set statistics",
    }


def compare_file_sketches(path_a: str | Path, path_b: str | Path, k: int,
                          w: int, canonical: bool = True,
                          order: str = "hash") -> dict:
    """Minimizer-sketch similarity estimate between two files; each file
    pools the per-record minimizer sketches into one set (union semantics).
    Estimates, not exact set statistics."""
    pooled = []
    for path in (path_a, path_b):
        s: set = set()
        for seq in load_sequences(path):
            s |= set(minimizers(seq, k, w, canonical, order))
        pooled.append(s)
    a, b = pooled
    j = jaccard(a, b)
    return {
        "mode": "minimizer-sketch", "k": k, "w": w, "order": order,
        "canonical": canonical,
        "file_a": str(path_a), "file_b": str(path_b),
        "sketch_a": len(a), "sketch_b": len(b), "shared": len(a & b),
        "jaccard_estimate": j,
        "containment_a_in_b_estimate": containment(a, b),
        "containment_b_in_a_estimate": containment(b, a),
        "mash_distance": mash_distance(j, k),
        "note": "sketch estimates, not exact set statistics",
    }
