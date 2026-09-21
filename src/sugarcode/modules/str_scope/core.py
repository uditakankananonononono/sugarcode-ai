from __future__ import annotations
import math
from collections import Counter
from ...bio.sequence import clean_dna


def find_strs(seq: str, min_unit: int = 1, max_unit: int = 6, min_repeats: int = 4) -> list[dict]:
    """Exact tandem-repeat detection over 1-6 bp units (suffix-comparison scan)."""
    s = clean_dna(seq)
    n = len(s)
    hits = []
    i = 0
    while i < n:
        best = None
        for u in range(min_unit, max_unit + 1):
            if i + 2 * u > n:
                continue
            unit = s[i:i + u]
            reps = 1
            while s[i + reps * u:i + (reps + 1) * u] == unit:
                reps += 1
            if reps >= min_repeats:
                cand = {"start": i, "unit": unit, "unit_len": u,
                        "repeats": reps, "length": reps * u}
                if best is None or cand["length"] > best["length"]:
                    best = cand
        if best:
            hits.append(best)
            i = best["start"] + best["length"]
        else:
            i += 1
    return hits


def expansion_call(sample_repeats: int, reference_repeats: int, unit: str = "") -> dict:
    """Classify an STR genotype vs reference (normal/intermediate/expanded)."""
    delta = sample_repeats - reference_repeats
    if delta <= 2:
        cls = "normal range"
    elif delta <= 10:
        cls = "intermediate / premutation range"
    else:
        cls = "expanded - pathogenic-range candidate"
    return {
        "unit": unit,
        "reference_repeats": reference_repeats,
        "sample_repeats": sample_repeats,
        "delta": delta,
        "classification": cls,
        "instability_risk": round(1 - math.exp(-max(delta, 0) / 12.0), 3),
    }


def diagnostic_index(str_loci: list[dict], repair_pathway_links: int = 0) -> dict:
    """Diagnostic potential index across loci.

    Combines expansion burden, motif pathogenicity priors (CAG/CTG/CGG known
    expansion disease motifs) and DNA-repair-pathway disruption links.
    """
    hot = {"CAG", "CTG", "CGG", "GCC", "GAA", "CAGG", "CCTG"}
    score = 0.0
    annotated = []
    for locus in str_loci:
        unit = locus["unit"].upper()
        delta = locus.get("delta", 0)
        w = 1.5 if unit in hot or unit[::-1] in hot else 1.0
        contrib = w * min(max(delta, 0) / 10.0, 3.0)
        score += contrib
        annotated.append({**locus, "hot_motif": unit in hot, "contribution": round(contrib, 3)})
    score += 0.5 * repair_pathway_links
    index = round(1 - math.exp(-score / 5.0), 3)
    return {
        "diagnostic_potential_index": index,
        "loci": annotated,
        "repair_pathway_links": repair_pathway_links,
        "interpretation": ("high" if index > 0.6 else "moderate" if index > 0.3 else "low")
        + " diagnostic potential for repeat-instability disease",
    }
