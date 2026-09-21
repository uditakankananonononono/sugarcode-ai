from __future__ import annotations
import math
from collections import Counter
from ...bio.sequence import clean_dna, gc_content, find_motif, reverse_complement
from ..dark_genome.core import TF_MOTIFS
from ..openclinvar.core import interpret_variant


def _kmer_zscores(s: str, k: int = 6) -> list[dict]:
    """Over/under-represented k-mers vs mononucleotide expectation (z-score)."""
    n = len(s) - k + 1
    if n <= 0:
        return []
    counts = Counter(s[i:i + k] for i in range(n))
    p = {b: s.count(b) / len(s) for b in "ACGT"}
    out = []
    for kmer, c in counts.items():
        exp = n
        for b in kmer:
            exp *= p.get(b, 0.001)
        if exp < 1:
            continue
        z = (c - exp) / math.sqrt(exp)
        if abs(z) >= 3:
            out.append({"kmer": kmer, "count": c, "expected": round(exp, 2),
                        "z": round(z, 2)})
    return sorted(out, key=lambda x: -abs(x["z"]))[:20]


def analyze_sequence(seq: str) -> dict:
    """Regulatory-motif and compositional analysis of raw sequence at scale."""
    s = clean_dna(seq)
    motifs = []
    for name, motif in TF_MOTIFS.items():
        for pos in find_motif(s, motif):
            motifs.append({"tf": name, "position": pos})
    # CTCF is the canonical loop-anchor factor; scan its motif explicitly
    ctcf = find_motif(s, "CCGCGNGGNGGCAG")
    return {
        "length": len(s),
        "gc_content": round(gc_content(s), 4),
        "tf_motifs": sorted(motifs, key=lambda m: m["position"]),
        "ctcf_sites": ctcf,
        "kmer_anomalies": _kmer_zscores(s),
        "long_range": predict_loops(s),
    }


def predict_loops(seq: str, min_span: int = 2000) -> list[dict]:
    """Predict 3D chromatin loops from convergent CTCF motif pairs.

    Loop anchors form between a forward-strand CTCF and a downstream
    reverse-strand CTCF (convergent orientation rule).
    """
    s = clean_dna(seq)
    motif = "CCGCGNGGNGGCAG"
    fwd = find_motif(s, motif)
    rev = [len(s) - p - len(motif) for p in find_motif(reverse_complement(s), motif)]
    loops = []
    for a in fwd:
        for b in rev:
            if b - a >= min_span:
                loops.append({"anchor1": a, "anchor2": b, "span": b - a,
                              "orientation": "convergent",
                              "confidence": round(min(1.0, 20000 / (b - a)), 3)})
    return sorted(loops, key=lambda l: -l["confidence"])


def interpret_sequence_variant(gene: str, seq_context: str, pos: int, alt: str,
                               **kwargs) -> dict:
    """Clinical reading of a variant inside its sequence context.

    Combines codon-level consequence with motif-disruption analysis: does the
    change break a TF motif or CTCF anchor?
    """
    s = clean_dna(seq_context)
    if not 0 <= pos < len(s):
        raise ValueError("pos outside context")
    ref = s[pos]
    alt = clean_dna(alt)[0]
    mutant = s[:pos] + alt + s[pos + 1:]
    broken, created = [], []
    for name, motif in TF_MOTIFS.items():
        ref_hits = set(find_motif(s, motif))
        alt_hits = set(find_motif(mutant, motif))
        for h in ref_hits - alt_hits:
            if h <= pos < h + len(motif):
                broken.append({"tf": name, "position": h})
        for h in alt_hits - ref_hits:
            if h <= pos < h + len(motif):
                created.append({"tf": name, "position": h})
    base = interpret_variant(gene, f"c.{pos + 1}{ref}>{alt}", **kwargs)
    reg_impact = "regulatory (non-coding context)" if broken or created else "no motif impact detected"
    return {
        **base,
        "ref_base": ref, "alt_base": alt,
        "motifs_broken": broken, "motifs_created": created,
        "regulatory_impact": reg_impact,
        "noncoding_note": ("Variant alters a regulatory element; can influence gene "
                           "regulation without changing any protein." if broken or created
                           else "No regulatory motif effect found in this context."),
    }
