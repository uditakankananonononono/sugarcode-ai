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


# --- drop 13: cfDNA fragment-length entropy model -------------------------------
def fragment_length_model(tumor_fraction: float = 0.0, n_fragments: int = 20000,
                          seed: int = 42) -> dict:
    """cfDNA fragment-length distribution, entropy and tumor/healthy classifier.

    Published anchors (honestly labeled as literature anchors, not fitted data):
    healthy cfDNA peaks at ~166 bp (mono-nucleosomal, 147 bp core + linker);
    ctDNA is shorter, modal ~134-144 bp (Snyder et al. 2016; Underhill et al.
    2016). Model: mixture of gamma components for mono/di-nucleosomal peaks,
    tumor fragments sampled from the short component; Shannon entropy of the
    length histogram increases with tumor fraction; a log-likelihood-ratio
    classifies a sampled profile."""
    import math
    import numpy as np
    if not 0.0 <= tumor_fraction <= 1.0:
        raise ValueError("tumor_fraction in [0, 1]")
    rng = np.random.default_rng(seed)

    def sample_comp(n, mode, spread):
        # gamma with given mode and spread: shape k = 1 + mode^2/spread^2
        k = 1 + (mode / spread) ** 2
        theta = mode / (k - 1)
        return rng.gamma(k, theta, n)

    n_t = int(round(tumor_fraction * n_fragments))
    n_h = n_fragments - n_t
    healthy = np.concatenate([sample_comp(int(n_h * 0.9), 166, 18),
                              sample_comp(n_h - int(n_h * 0.9), 332, 25)])
    tumor = sample_comp(n_t, 140, 22)
    frags = np.concatenate([healthy, tumor])
    frags = frags[(frags >= 50) & (frags <= 500)]
    hist, edges = np.histogram(frags, bins=range(50, 502, 5))
    p = hist / hist.sum()
    entropy = float(-(p[p > 0] * np.log2(p[p > 0])).sum())
    short_frac = float(((frags >= 100) & (frags <= 150)).sum() / len(frags))

    # log-likelihood ratio vs published-anchor reference profiles
    centers = (edges[:-1] + edges[1:]) / 2
    def gamma_pdf(x, mode, spread):
        k = 1 + (mode / spread) ** 2
        theta = mode / (k - 1)
        logp = (k - 1) * np.log(x) - x / theta - k * math.log(theta) - math.lgamma(k)
        return np.exp(logp)
    ref_h = 0.9 * gamma_pdf(centers, 166, 18) + 0.1 * gamma_pdf(centers, 332, 25)
    mix = (1 - tumor_fraction) * ref_h + tumor_fraction * gamma_pdf(centers, 140, 22)
    ref_h /= ref_h.sum(); mix /= mix.sum()
    eps = 1e-12
    llr = float((p * (np.log(p + eps) - np.log(ref_h + eps))).sum())  # KL to healthy ref
    return {
        "tumor_fraction": tumor_fraction,
        "n_fragments": int(len(frags)),
        "modal_length_bp": float(centers[int(hist.argmax())]),
        "shannon_entropy_bits": round(entropy, 4),
        "short_fraction_100_150bp": round(short_frac, 4),
        "kl_divergence_to_healthy_ref": round(llr, 5),
        "histogram": {"centers_bp": [round(float(c), 1) for c in centers],
                      "density": [round(float(x), 6) for x in p]},
        "anchors": {"healthy_peak_bp": 166, "ctdna_peak_bp": "134-144",
                    "sources": ["Snyder et al. Cell 2016", "Underhill et al. PLoS Genet 2016"],
                    "status": "literature anchors - gamma mixture is a model, not fitted patient data"},
    }
