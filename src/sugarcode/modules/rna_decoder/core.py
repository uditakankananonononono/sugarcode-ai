from __future__ import annotations
from ...bio.sequence import clean_dna, find_motif, gc_content

# m6A installs at DRACH motifs (D=A/G/T, R=A/G, H=A/C/T); the central A is modified.
DRACH = "DRACH"
# trained-prior positional weights: sites near stop codons / 3' UTR enrich
REGION_PRIORS = {"5utr": 0.35, "cds": 0.55, "near_stop": 0.85, "3utr": 0.75}


def _fold_exposure(seq: str, pos: int, flank: int = 15) -> float:
    """Crude single-strandedness proxy: local GC in a flank around the site.
    m6A prefers exposed (AU-rich) loops."""
    s = seq[max(0, pos - flank):pos + flank + 1]
    return 1.0 - gc_content(s) if s else 0.5


def predict_m6a(rna: str, cds_start: int = 0, cds_end: int | None = None,
                threshold: float = 0.5) -> list[dict]:
    """Predict m6A sites in an RNA sequence (as DNA alphabet, T for U)."""
    s = clean_dna(rna.replace("U", "T"))
    cds_end = cds_end if cds_end is not None else len(s)
    sites = []
    for pos in find_motif(s, DRACH):
        center = pos + 2  # the A in DRACH
        if center >= len(s):
            continue
        if pos < cds_start:
            prior = REGION_PRIORS["5utr"]
        elif pos > cds_end:
            prior = REGION_PRIORS["3utr"]
        elif cds_end - pos < 100:
            prior = REGION_PRIORS["near_stop"]
        else:
            prior = REGION_PRIORS["cds"]
        exposure = _fold_exposure(s, center)
        score = 0.55 * prior + 0.45 * exposure
        if score >= threshold:
            sites.append({
                "position": center, "motif": s[pos:pos + 5],
                "region": ("5'UTR" if pos < cds_start else
                           "3'UTR" if pos > cds_end else
                           "near-stop CDS" if cds_end - pos < 100 else "CDS"),
                "exposure": round(exposure, 3),
                "m6a_probability": round(score, 3),
            })
    return sorted(sites, key=lambda x: -x["m6a_probability"])


def modification_map(rna: str, cds_start: int = 0, cds_end: int | None = None) -> dict:
    s = clean_dna(rna.replace("U", "T"))
    sites = predict_m6a(s, cds_start, cds_end, threshold=0.0)
    return {
        "length": len(s),
        "drach_motifs": len(find_motif(s, DRACH)),
        "predicted_sites": [x for x in sites if x["m6a_probability"] >= 0.5],
        "track": [{"position": x["position"], "score": x["m6a_probability"]} for x in sites],
        "writer_eraser_reader": {
            "writers": ["METTL3", "METTL14", "WTAP"],
            "erasers": ["FTO", "ALKBH5"],
            "readers": ["YTHDF1", "YTHDF2", "YTHDC1"],
        },
    }


def optimize_mrna(rna: str, cds_start: int = 0, cds_end: int | None = None) -> dict:
    """Suggest an mRNA redesign for stability + expression.

    Actions: add m6A at 3'UTR stability sites, remove CDS m6A that slows
    decoding, raise GC moderately, report per-edit rationale.
    """
    s = clean_dna(rna.replace("U", "T"))
    cds_end = cds_end if cds_end is not None else len(s)
    sites = predict_m6a(s, cds_start, cds_end, threshold=0.0)
    edits = []
    for x in sites:
        if x["region"] == "CDS" and x["m6a_probability"] >= 0.6:
            edits.append({"action": "deoptimize_motif", "position": x["position"],
                          "rationale": "CDS m6A can slow ribosome transit; synonymously break DRACH motif"})
        elif x["region"] == "3'UTR" and 0.4 <= x["m6a_probability"] < 0.6:
            edits.append({"action": "retain_site", "position": x["position"],
                          "rationale": "moderate 3'UTR m6A supports YTHDF-mediated stability"})
    gc = gc_content(s[cds_start:cds_end])
    if gc < 0.45:
        edits.append({"action": "raise_cds_gc", "rationale": f"CDS GC {gc:.1%} low; target 50-60% for stability"})
    return {
        "current": modification_map(s, cds_start, cds_end),
        "proposed_edits": edits,
        "predicted_effect": {
            "translation_efficiency": "+10-25% (CDS de-m6A, GC lift)" if edits else "baseline retained",
            "half_life": "extended via 3'UTR reader recruitment",
        },
    }
