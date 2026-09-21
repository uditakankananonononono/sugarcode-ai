from __future__ import annotations
from ...bio.sequence import clean_dna, gc_content
from ..crispr_opt.core import design_guides
from ..dark_genome.core import TF_MOTIFS
from ...bio.sequence import find_motif

HISTONE_MARKS = {
    "H3K4me3": "active promoter", "H3K27ac": "active enhancer",
    "H3K27me3": "polycomb repression", "H3K9me3": "constitutive heterochromatin",
    "H3K36me3": "transcribed gene body",
}


def chromatin_landscape(seq: str, promoter_span: tuple[int, int] | None = None) -> dict:
    """Sequence-informed chromatin landscape: accessibility proxy + mark map.

    Accessibility proxy: AT-rich + TF-motif-dense windows score open;
    GC/CpG-dense promoter windows get H3K4me3; repeats get H3K9me3.
    """
    s = clean_dna(seq)
    window = 200
    track = []
    for i in range(0, len(s) - window + 1, window // 2):
        w = s[i:i + window]
        gc = gc_content(w)
        tf_hits = sum(len(find_motif(w, m)) for m in TF_MOTIFS.values())
        cpg = w.count("CG")
        accessibility = min(1.0, 0.3 * (1 - gc) + 0.5 * min(tf_hits / 5.0, 1.0) + 0.2 * min(cpg / 10.0, 1.0))
        marks = []
        if cpg >= 8 and gc > 0.5:
            marks.append("H3K4me3")
        if tf_hits >= 2 and accessibility > 0.5:
            marks.append("H3K27ac")
        if gc < 0.35 and tf_hits == 0:
            marks.append("H3K9me3")
        track.append({"start": i, "end": i + window, "gc": round(gc, 3),
                      "tf_motifs": tf_hits, "accessibility": round(accessibility, 3),
                      "marks": marks})
    in_promoter = None
    if promoter_span:
        a, b = promoter_span
        in_promoter = [t for t in track if t["start"] < b and t["end"] > a]
    return {"length": len(s), "track": track,
            "promoter_region": in_promoter,
            "mark_legend": HISTONE_MARKS}


def design_epigenome_edit(seq: str, target_span: tuple[int, int], mode: str = "CRISPRi",
                          background: str | None = None) -> dict:
    """Design a CRISPRa/i perturbation without altering DNA sequence.

    mode CRISPRi: dCas9-KRAB guides at promoter to repress.
    mode CRISPRa: dCas9-VP64/p300 guides upstream of TSS to activate.
    Guide placement: CRISPRi -50..+300 around TSS; CRISPRa -400..-50 upstream.
    Returns ranked guides with chromatin context and predicted effect.
    """
    if mode not in ("CRISPRi", "CRISPRa"):
        raise ValueError("mode must be CRISPRi or CRISPRa")
    s = clean_dna(seq)
    a, b = target_span
    if mode == "CRISPRi":
        lo, hi = max(0, a - 50), min(len(s), a + 300)
    else:
        lo, hi = max(0, a - 400), max(0, a - 50)
    region = s[lo:hi] if hi > lo else s[max(0, a - 300):a + 100]
    designs = design_guides(region, background=background, top_n=5)
    landscape = chromatin_landscape(s, target_span)
    open_frac = _open_fraction(landscape, (lo, hi))
    effect = _predict_effect(mode, designs["guides"], open_frac)
    return {
        "mode": mode,
        "target_span": target_span,
        "guide_window": [lo, hi],
        "guides": designs["guides"],
        "chromatin": landscape,
        "window_open_chromatin_fraction": open_frac,
        "predicted_effect": effect,
        "non_permanent": True,
        "mechanism": ("dCas9-KRAB: H3K9me3 deposition, local heterochromatin, reversible repression"
                      if mode == "CRISPRi" else
                      "dCas9-VP64/p300: H3K27ac deposition, chromatin opening, reversible activation"),
    }


def _open_fraction(landscape: dict, span: tuple[int, int]) -> float:
    a, b = span
    tiles = [t for t in landscape["track"] if t["start"] < b and t["end"] > a]
    if not tiles:
        return 0.0
    return round(sum(t["accessibility"] for t in tiles) / len(tiles), 3)


def _predict_effect(mode: str, guides: list[dict], open_frac: float) -> dict:
    if not guides:
        return {"fold_change": 1.0, "confidence": "no guides available"}
    best = guides[0]["composite"]
    if mode == "CRISPRi":
        fold = max(0.05, 1.0 - 0.8 * best * (0.5 + open_frac))
        return {"fold_change": round(fold, 3), "direction": "repression",
                "confidence": "higher on open chromatin with strong guides"}
    fold = 1.0 + 6.0 * best * (1.0 - 0.5 * open_frac)
    return {"fold_change": round(fold, 3), "direction": "activation",
            "confidence": "largest gains on closed/naive chromatin"}
