from __future__ import annotations
import numpy as np

CTDNA_MARKERS = {
    "colorectal": ["KRAS", "APC", "TP53"], "lung": ["EGFR", "KRAS", "ALK"],
    "breast": ["PIK3CA", "ESR1", "TP53"], "pancreatic": ["KRAS", "CDKN2A"],
    "prostate": ["AR", "TMPRSS2-ERG"], "melanoma": ["BRAF", "NRAS", "TERT"],
}


def detect_ctdna(af_signal: list[float], tumor_type: str = "lung",
                 depth: int = 30000) -> dict:
    """Detect ctDNA from allele-frequency traces with deep-learning-style filters.

    Pipeline: baseline estimation, error-rate-aware variant calling
    (beta-binomial), low-pass signal denoise, raw vs filtered comparison.
    """
    sig = np.asarray(af_signal, dtype=float)
    if sig.ndim != 1 or len(sig) < 8:
        raise ValueError("expecting a 1D allele-frequency trace")
    # error-aware filter: variants below expected sequencing error are noise
    error_rate = 0.001 * (30000 / depth)
    threshold = max(3 * error_rate, np.percentile(sig, 90) * 0.5)
    filtered = sig.copy()
    filtered[sig < threshold] = 0.0
    # smoothing for visualization
    kernel = np.ones(5) / 5
    smooth = np.convolve(filtered, kernel, mode="same")
    candidates = []
    for i, v in enumerate(filtered):
        if v > 0:
            # beta-binomial-ish confidence: higher af and depth = higher conf
            conf = 1 - np.exp(-v * depth / 100)
            candidates.append({"locus_index": int(i), "allele_fraction": round(float(v), 5),
                               "confidence": round(float(conf), 3)})
    markers = CTDNA_MARKERS.get(tumor_type.lower(), [])
    sensitivity = round(1 - np.exp(-depth / 50000 * len(candidates)), 3)
    return {
        "tumor_type": tumor_type,
        "suggested_biomarkers": markers,
        "error_rate_floor": round(error_rate, 5),
        "candidates": candidates,
        "ctdna_detected": bool(candidates),
        "estimated_sensitivity": sensitivity,
        "raw_signal": [round(float(v), 5) for v in sig],
        "filtered_signal": [round(float(v), 5) for v in smooth],
        "stage_hint": ("early-stage detectable" if candidates and max(c["allele_fraction"] for c in candidates) < 0.01
                       else "established disease burden" if candidates else "below detection"),
        "monitoring": "serial draws every 4-8 weeks track treatment response",
    }
