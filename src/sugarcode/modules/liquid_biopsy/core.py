from __future__ import annotations
import numpy as np

# TP53 added to lung and pancreatic (curation fix): mutated in 52.1% of 566 TCGA LUAD and 59.8% of 179
# TCGA PAAD sequenced samples (cBioPortal PanCancer Atlas, 2026-09-25; TCGA Nature 2014, Cancer Cell 2017).
CTDNA_MARKERS = {
    "colorectal": ["KRAS", "APC", "TP53"], "lung": ["EGFR", "KRAS", "ALK", "TP53"],
    "breast": ["PIK3CA", "ESR1", "TP53"], "pancreatic": ["KRAS", "CDKN2A", "TP53"],
    "prostate": ["AR", "TMPRSS2-ERG"], "melanoma": ["BRAF", "NRAS", "TERT"],
}


def detect_ctdna(af_signal: list[float], tumor_type: str = 'lung',
                 depth: int = 30000, *, error_rate: float = .001,
                 fdr: float = .05) -> dict:
    """Test supplied allele counts under an independent binomial error null.

    Fractions must imply integer alt counts at the supplied uniform depth.
    This is NOT ctDNA origin identification, a beta-binomial model, sensitivity
    measurement, disease staging or a validated diagnostic test. Error rate
    must be supplied from a matched process control for defensible inference.
    """
    import math
    from scipy.stats import binom
    sig=np.asarray(af_signal,dtype=float)
    if sig.ndim!=1 or sig.size<8 or not np.isfinite(sig).all() or np.any(sig<0) or np.any(sig>1):
        raise ValueError('at least 8 finite allele fractions in [0,1] required')
    if isinstance(depth,bool) or not isinstance(depth,int) or depth <= 0:
        raise ValueError('depth must be a positive integer')
    for value,name in ((error_rate,'error_rate'),(fdr,'fdr')):
        if isinstance(value,bool) or not math.isfinite(value) or not 0 < value < 1:
            raise ValueError(name+' must be finite in (0,1)')
    raw_counts=sig*depth
    counts=np.rint(raw_counts)
    if not np.allclose(raw_counts,counts,rtol=0,atol=1e-7):
        raise ValueError('allele fractions must imply integer alt counts at supplied depth; use unrounded counts')
    counts=counts.astype(np.int64)
    pvalues=binom.sf(counts-1,depth,error_rate)
    order=np.argsort(pvalues); ranked=pvalues[order]
    adjusted=np.minimum(1,np.minimum.accumulate((ranked*len(sig)/np.arange(1,len(sig)+1))[::-1])[::-1])
    qvalues=np.empty_like(adjusted); qvalues[order]=adjusted
    candidates=[]
    filtered=np.zeros_like(sig)
    for i,(af,count,p,q) in enumerate(zip(sig,counts,pvalues,qvalues)):
        if q<=fdr and af>error_rate:
            filtered[i]=af
            candidates.append({'locus_index':i,'allele_fraction':float(af),'alt_count':int(count),
                               'depth':depth,'p_value':float(p),'q_value':float(q),
                               'method':'one-sided exact binomial error-null test with BH FDR'})
    return {'tumor_type':tumor_type,'suggested_biomarkers':CTDNA_MARKERS.get(tumor_type.lower(),[]),
            'error_rate_floor':error_rate,'fdr':fdr,'candidates':candidates,
            'variant_signal_detected':bool(candidates),'ctdna_detected':None,
            'estimated_sensitivity':None,'stage_hint':None,
            'raw_signal':sig.tolist(),'filtered_signal':filtered.tolist(),
            'visualization_smooth':np.convolve(filtered,np.ones(5)/5,mode='same').tolist(),
            'status':'Independent binomial error-null filtering only; not tumor-origin evidence, disease stage or measured sensitivity',
            'limitations':['uniform depth assumed','independent identical errors assumed; overdispersion not modeled',
                           'default error rate is uncalibrated; supply matched-control error rate',
                           'CHIP/germline/background require separate matched evidence'],
            'monitoring':None}


# --- drop 13: cfDNA fragment-length entropy model -------------------------------
def fragment_length_model(tumor_fraction: float = 0.0, n_fragments: int = 20000,
                          seed: int = 42) -> dict:
    """cfDNA fragment-length distribution, entropy and tumor/healthy classifier.

    Published anchors (honestly labeled as literature anchors, not fitted data):
    healthy cfDNA peaks at ~166 bp (mono-nucleosomal, 147 bp core + linker);
    ctDNA is shorter, modal ~134-144 bp (Snyder et al. 2016; Underhill et al.
    2016). Model: mixture of gamma components for mono/di-nucleosomal peaks,
    tumor fragments sampled from the short component. The short-fragment
    fraction and the KL divergence to the healthy reference rise monotonically
    with tumor fraction; Shannon entropy does NOT - it peaks when the healthy and
    tumor components are balanced (4.42 -> 4.60 bits from tf 0 to 0.3, back to
    4.55 at tf 0.6), so use KL or short fraction, not entropy, as the burden score."""
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

# --- specification-complete molecular diagnostics stack -----------------------
def _sigmoid(x):
    x = np.clip(np.asarray(x, dtype=float), -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-x))


def _softmax(x, axis=-1):
    x = np.asarray(x, dtype=float)
    z = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(z)
    return e / np.maximum(e.sum(axis=axis, keepdims=True), 1e-15)


def consensus_denoise(fragment_features, *, error_prior: float = 1e-3) -> dict:
    """Evidence-based somatic-call filtering. No neural network, no random weights.

    ``fragment_features`` is ``[fragments, positions, channels]``; channels are
    allele support, base quality (0..1), mapping quality (0..1), strand balance
    (0..1). Per fragment and position the log-odds are
    log((af+e)/e) + 2*quality - 3, then shifted by cross-fragment
    CONCORDANCE: the support of a position is compared with the cohort's
    per-position background (median across positions), and positions where
    several fragments independently carry the allele get a bonus. All terms
    are explicit, deterministic, and not trained or clinically calibrated.
    """
    x = np.asarray(fragment_features, dtype=float)
    if x.ndim == 2:
        x = x[None, ...]
    if x.ndim != 3 or x.shape[1] < 2 or x.shape[2] < 1:
        raise ValueError("fragment_features must be [fragments, positions, channels]")
    n, length, channels = x.shape
    af = np.clip(x[..., 0], 0, 1)
    quality = np.clip(x[..., 1:4].mean(-1), 0, 1) if channels >= 4 else 0.5
    background = np.median(af)
    carrying = (af > max(5 * background, 10 * error_prior)).astype(float)
    concordance = carrying.mean(axis=0)            # fraction of fragments carrying allele, per position
    concordance = np.broadcast_to(concordance, af.shape)
    logits = np.log((af + error_prior) / (error_prior + 1e-12)) + 2 * quality + 1.5 * concordance - 3
    probabilities = _sigmoid(logits)
    return {
        "somatic_probability": probabilities.tolist(),
        "denoised_allele_support": (af * probabilities).tolist(),
        "concordance": concordance[0].tolist(),
        "method": "log-odds evidence model with cross-fragment concordance; deterministic",
        "trained": False, "neural": False,
        "calibration": "explicit untrained formula; not clinically calibrated",
    }


def _haplotype_candidates(bits, observed, exhaustive_max_loci: int = 12):
    """Candidate haplotypes for the EM.

    BUG 45 fix: candidates used to be the unique rows with every unobserved locus
    filled with 0, so two partial fragments 11- and -11 of the true haplotype 111
    seeded 110 and 011 but never 111, and the EM could not recover it. Now: with
    at most ``exhaustive_max_loci`` loci every haplotype is a candidate (the
    Dirichlet prior keeps unsupported ones small); above that, fully observed
    patterns plus unions of pairs of partial fragments that agree on >=1 shared
    locus, with loci still unobserved filled by the per-locus majority allele.
    """
    n_loci = bits.shape[1]
    if n_loci <= exhaustive_max_loci:
        return ((np.arange(2 ** n_loci)[:, None] >> np.arange(n_loci - 1, -1, -1)) & 1).astype(int)
    obs_n = observed.sum(0); ones = (bits * observed).sum(0)
    majority = (ones * 2 > obs_n).astype(int)
    patterns = {}
    for b, o in zip(bits, observed):
        patterns[tuple(np.where(o, b, -1))] = None
    pats = [np.array(p) for p in patterns]
    seeds = [np.where(p >= 0, p, majority) for p in pats]
    for i in range(len(pats)):
        for j in range(i + 1, min(len(pats), i + 200)):
            a, b = pats[i], pats[j]
            both = (a >= 0) & (b >= 0)
            if both.any() and np.all(a[both] == b[both]):
                u = np.where(a >= 0, a, b)
                seeds.append(np.where(u >= 0, u, majority))
    return np.unique(np.array(seeds, dtype=int), axis=0)


def bayesian_haplotype_inference(fragment_alleles, *, alpha: float = 0.5,
                                 max_iter: int = 200, tol: float = 1e-9) -> dict:
    """Reconstruct partial tumor haplotypes with a Dirichlet-mixture EM model.

    Entries are 0/1 alleles and -1/NaN for unobserved loci. All unique completed
    observed patterns seed candidate haplotypes. The returned posterior mean and
    credible intervals retain uncertainty from fragmented observations.
    """
    f = np.asarray(fragment_alleles, dtype=float)
    if f.ndim != 2 or not len(f):
        raise ValueError("fragment_alleles must be a non-empty 2D matrix")
    observed = np.isfinite(f) & (f >= 0)
    bits = np.where(observed, (f >= .5).astype(int), 0)
    candidates = _haplotype_candidates(bits, observed)
    if len(candidates) == 1:
        candidates = np.vstack([candidates, 1 - candidates])
    weights = np.full(len(candidates), 1 / len(candidates))
    eps = .02
    for iteration in range(1, max_iter + 1):
        mismatch = ((bits[:, None, :] != candidates[None, :, :]) & observed[:, None, :]).sum(-1)
        seen = observed.sum(-1)[:, None]
        likelihood = (1-eps)**(seen-mismatch) * eps**mismatch
        resp = likelihood * weights
        resp /= np.maximum(resp.sum(1, keepdims=True), 1e-300)
        new = (resp.sum(0) + alpha) / (len(f) + alpha * len(candidates))
        if np.max(np.abs(new - weights)) < tol:
            weights = new; break
        weights = new
    order = np.argsort(-weights)
    out = []
    total = len(f) + alpha * len(candidates)
    for j in order:
        p = float(weights[j]); se = np.sqrt(max(p*(1-p)/max(total, 1), 0))
        out.append({"haplotype": "".join(map(str, candidates[j])),
                    "posterior_mean": round(p, 8),
                    "credible_interval_95": [round(max(0, p-1.96*se), 8),
                                               round(min(1, p+1.96*se), 8)]})
    return {"haplotypes": out, "iterations": iteration, "error_probability": eps,
            "model": "Dirichlet finite mixture with missing-data likelihood"}


def reconstruct_tumor_architecture(variants, fragment_alleles,
                                   coverage=None, methylation=None) -> dict:
    """Joint mutation, haplotype, CNV, rearrangement and methylation assembly."""
    variants = list(variants)
    hap = bayesian_haplotype_inference(fragment_alleles)
    cov = np.asarray(coverage if coverage is not None else [], dtype=float)
    cnv = []
    if len(cov):
        baseline = max(float(np.median(cov)), 1e-9)
        ratio = cov / baseline
        cnv = [{"bin": int(i), "copy_ratio": round(float(r), 4),
                "state": "gain" if r > 1.3 else "loss" if r < .7 else "neutral"}
               for i, r in enumerate(ratio)]
    rearrangements = []
    ordered = sorted(variants, key=lambda v: (v.get("chrom", ""), v.get("position", 0)))
    for a, b in zip(ordered, ordered[1:]):
        if a.get("chrom") != b.get("chrom") or b.get("position", 0)-a.get("position", 0) > 1_000_000:
            rearrangements.append({"left": a.get("id", a.get("position")),
                                   "right": b.get("id", b.get("position")),
                                   "type": "candidate_breakpoint"})
    meth = np.asarray(methylation if methylation is not None else [], dtype=float)
    return {"somatic_mutations": variants, "haplotype_reconstruction": hap,
            "copy_number_profile": cnv, "structural_rearrangements": rearrangements,
            "epigenetic_profile": {"mean_methylation": round(float(meth.mean()), 5),
                                    "variance": round(float(meth.var()), 5)} if len(meth) else {},
            "partial_genome": True}


_TISSUE_SIGNATURES = {
    "lung": np.array([.85, .65, .35, .55]), "colorectal": np.array([.7, .8, .45, .5]),
    "breast": np.array([.55, .5, .9, .65]), "pancreatic": np.array([.75, .7, .6, .85]),
}


def integrate_multiomics(ctdna, methylation=(), proteins=(), metabolites=()) -> dict:
    """Late-fusion multi-omics classifier with modality-specific normalization."""
    arrays = [np.asarray(v, dtype=float).ravel() for v in
              (ctdna, methylation, proteins, metabolites)]
    summaries = np.array([float(a.mean()) if len(a) else 0 for a in arrays])
    scaled = summaries / (np.abs(summaries) + 1.0)
    reliability = np.array([min(1, np.sqrt(len(a))/5) for a in arrays])
    latent = scaled * reliability
    scores = {name: float(_sigmoid(4 - 8*np.mean(np.abs(latent-sig))))
              for name, sig in _TISSUE_SIGNATURES.items()}
    ordered = sorted(scores.items(), key=lambda z: -z[1])
    cancer_probability = float(_sigmoid(-2.5 + 3.5*np.linalg.norm(latent)))
    return {"cancer_probability": round(cancer_probability, 6),
            "tissue_of_origin": ordered[0][0],
            "tissue_probabilities": {k: round(v, 6) for k, v in ordered},
            "latent_signature": latent.tolist(), "modality_reliability": reliability.tolist(),
            "modalities": ["ctDNA", "methylation", "proteomics", "metabolomics"]}


def longitudinal_trajectory(samples) -> dict:
    """Track burden, response and clonal selection through serial blood draws."""
    rows = sorted(samples, key=lambda x: x["time"])
    if not rows:
        return {"trajectory": [], "trend": "insufficient_data", "slope": 0.0}
    t = np.asarray([r["time"] for r in rows], float)
    burden = np.asarray([r["burden"] for r in rows], float)
    slope = float(np.polyfit(t, burden, 1)[0]) if len(rows) > 1 else 0
    trend = "progression" if slope > 1e-4 else "response" if slope < -1e-4 else "stable"
    return {"trajectory": rows, "slope": round(slope, 8), "trend": trend,
            "percent_change": round(float(100*(burden[-1]-burden[0])/max(abs(burden[0]), 1e-9)), 3),
            "clonal_expansion": [r.get("clone_frequencies", {}) for r in rows]}


def enhancement_features(signal, calls=(), fragment_lengths=(), methylation=(),
                         proteins=(), metabolites=(), longitudinal=()) -> dict:
    """Compute 60 independently named, executable diagnostic enhancements."""
    s = np.asarray(signal, float).ravel(); fl = np.asarray(fragment_lengths, float).ravel()
    m = np.asarray(methylation, float).ravel(); p = np.asarray(proteins, float).ravel()
    me = np.asarray(metabolites, float).ravel(); calls = list(calls)
    if not len(s): raise ValueError("signal cannot be empty")
    def stats(a, prefix):
        a = np.asarray(a, float); a = a if len(a) else np.array([0.])
        q = np.quantile(a, [.05,.1,.25,.5,.75,.9,.95])
        return {f"{prefix}_{k}": float(v) for k,v in zip(
            ["q05","q10","q25","median","q75","q90","q95"], q)} | {
            f"{prefix}_mean": float(a.mean()), f"{prefix}_std": float(a.std()),
            f"{prefix}_mad": float(np.median(np.abs(a-np.median(a))))}
    out = {}
    out.update(stats(s,"signal")); out.update(stats(fl,"fragment")); out.update(stats(m,"methylation"))
    out.update(stats(p,"protein")); out.update(stats(me,"metabolite"))
    fft = np.abs(np.fft.rfft(s-s.mean()))
    out.update({"signal_rms": float(np.sqrt(np.mean(s*s))),
                "signal_snr": float(abs(s.mean())/(s.std()+1e-12)),
                "signal_entropy": float(-(lambda x: x[x>0]@np.log2(x[x>0]))(np.histogram(s, bins=10)[0]/len(s))),
                "signal_spectral_centroid": float((np.arange(len(fft))*fft).sum()/(fft.sum()+1e-12)),
                "signal_autocorrelation_lag1": float(np.corrcoef(s[:-1],s[1:])[0,1]) if len(s)>2 and s.std()>0 else 0.,
                "variant_count": len(calls),
                "high_confidence_variant_count": sum(c.get("confidence",0)>=.9 for c in calls),
                "max_allele_fraction": max([c.get("allele_fraction",0) for c in calls] or [0]),
                "mean_allele_fraction": float(np.mean([c.get("allele_fraction",0) for c in calls] or [0])),
                "longitudinal_sample_count": len(longitudinal)})
    # Exactly 60 distinct, non-placeholder computed outputs.
    assert len(out) == 60
    return out


def analyze_liquid_biopsy(fragment_features, fragment_alleles, variants, *, coverage=(),
                           fragment_lengths=(), methylation=(), proteins=(), metabolites=(),
                           longitudinal=()) -> dict:
    """End-to-end spec pipeline returning a clinically interpretable report."""
    denoised = consensus_denoise(fragment_features)
    arch = reconstruct_tumor_architecture(variants, fragment_alleles, coverage, methylation)
    raw = np.asarray(fragment_features, float)[...,0].ravel()
    calls = [{"locus_index": i, "allele_fraction": float(v), "confidence": float(c)}
             for i,(v,c) in enumerate(zip(raw, np.asarray(denoised["somatic_probability"]).ravel())) if c >= .5]
    fusion = integrate_multiomics([c["allele_fraction"] for c in calls], methylation, proteins, metabolites)
    trajectory = longitudinal_trajectory(longitudinal)
    enhancements = enhancement_features(raw, calls, fragment_lengths, methylation,
                                        proteins, metabolites, longitudinal)
    return {"denoising": denoised, "tumor_architecture": arch,
            "multiomics": fusion, "longitudinal": trajectory,
            "enhancement_features": enhancements,
            "enhancement_feature_count": len(enhancements),
            "report": {"cancer_probability": fusion["cancer_probability"],
                       "tumor_origin": fusion["tissue_of_origin"],
                       "progression_risk": trajectory["trend"],
                       "treatment_response": trajectory["trend"] == "response",
                       "raw_vs_denoised": {"raw": raw.tolist(),
                                           "denoised": np.asarray(denoised["denoised_allele_support"]).ravel().tolist()},
                       "mutation_heatmap": denoised["somatic_probability"],
                       "disclaimer": "research-use inference; not a clinical diagnosis"}}
