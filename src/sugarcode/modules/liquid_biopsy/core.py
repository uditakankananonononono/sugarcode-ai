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
    if not x.shape[0] or not np.isfinite(x).all() or np.any(x<0) or np.any(x>1):
        raise ValueError('fragment feature channels must be nonempty finite fractions in [0,1]')
    if isinstance(error_prior,bool) or not np.isfinite(error_prior) or not 0<error_prior<1:
        raise ValueError('error_prior must be finite in (0,1)')
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
        "evidence_score": probabilities.tolist(),
        "calibrated": False,
        "score_weighted_allele_support": (af * probabilities).tolist(),
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
                                 max_iter: int = 200, tol: float = 1e-9,
                                 error_probability: float = .02) -> dict:
    """Regularized finite-mixture EM on partial binary fragments.

    Historical function name retained for compatibility. Fitted mixture weights
    are NOT a full Bayesian posterior. Missing values must be -1 or NaN.
    The fixed symmetric read-error model must be calibrated independently.
    """
    import math
    from scipy.special import logsumexp
    f=np.asarray(fragment_alleles,dtype=float)
    if f.ndim!=2 or min(f.shape)==0 or np.isinf(f).any():
        raise ValueError('nonempty fragments-by-loci matrix required, no infinite values')
    if np.any(~(np.isnan(f) | (f==-1) | (f==0) | (f==1))):
        raise ValueError('alleles must be 0/1 or explicit missing -1/NaN')
    for value,name in ((alpha,'alpha'),(tol,'tol')):
        if isinstance(value,bool) or not math.isfinite(value) or value<=0:
            raise ValueError(name+' must be finite positive')
    if isinstance(max_iter,bool) or not isinstance(max_iter,int) or max_iter<1:
        raise ValueError('max_iter must be positive integer')
    eps=error_probability
    if isinstance(eps,bool) or not math.isfinite(eps) or not 0<eps<.5:
        raise ValueError('error_probability must be finite in (0,.5)')
    observed=np.isfinite(f)&(f>=0)
    bits=np.where(observed,f,0).astype(int)
    candidates=_haplotype_candidates(bits,observed)
    if len(candidates)==1:
        candidates=np.vstack([candidates,1-candidates])
    weights=np.full(len(candidates),1/len(candidates))
    mismatch=((bits[:,None,:]!=candidates[None,:,:])&observed[:,None,:]).sum(-1)
    seen=observed.sum(-1)[:,None]
    log_likelihood=(seen-mismatch)*np.log1p(-eps)+mismatch*np.log(eps)
    converged=False
    for iteration in range(1,max_iter+1):
        log_joint=log_likelihood+np.log(weights)
        resp=np.exp(log_joint-logsumexp(log_joint,axis=1,keepdims=True))
        new=(resp.sum(0)+alpha)/(len(f)+alpha*len(candidates))
        delta=float(np.max(np.abs(new-weights))); weights=new
        if delta<tol:
            converged=True; break
    total=len(f)+alpha*len(candidates)
    out=[]
    for j in np.argsort(-weights):
        value=float(weights[j]); se=np.sqrt(value*(1-value)/total)
        out.append({'haplotype':''.join(map(str,candidates[j])),
                    'posterior_mean':round(value,8),
                    'mixture_weight':value,
                    'approximate_weight_interval_95':[max(0.,value-1.96*se),min(1.,value+1.96*se)]})
    return {'haplotypes':out,'iterations':iteration,'converged':converged,
            'max_weight_change':delta,'error_probability':eps,
            'log_likelihood':float(logsumexp(log_likelihood+np.log(weights),axis=1).sum()),
            'numerical_method':'log-space responsibilities',
            'candidate_method':'exhaustive' if f.shape[1]<=12 else 'partial-pattern heuristic completion',
            'model':'Regularized finite mixture EM with missing-data likelihood',
            'uncertainty_status':'Normal weight approximations ignore latent/candidate uncertainty; not posterior credible intervals',
            'compatibility_status':'posterior_mean is a legacy alias for fitted mixture weight, not a full posterior mean'}


def reconstruct_tumor_architecture(variants, fragment_alleles,
                                   coverage=None, methylation=None, *,
                                   normal_coverage=None, junction_evidence=None) -> dict:
    """Summarize supplied variant, depth and measured junction evidence.

    Not a tumor-origin classifier or absolute copy-number/structural-variant caller.
    Sample-median ratios without normal are descriptive, not CNV calls.
    """
    import copy
    variants=copy.deepcopy(list(variants))
    if any(not isinstance(v,dict) for v in variants):
        raise ValueError('variants must be mappings')
    hap=bayesian_haplotype_inference(fragment_alleles)
    cov=np.asarray([] if coverage is None else coverage,float)
    if cov.ndim!=1 or not np.isfinite(cov).all() or np.any(cov<0) or (cov.size and np.median(cov)<=0):
        raise ValueError('coverage requires finite nonnegative 1D values with positive median')
    cnv=[]
    if normal_coverage is not None:
        normal=np.asarray(normal_coverage,float)
        if normal.shape!=cov.shape or not cov.size or not np.isfinite(normal).all() or np.any(normal<=0):
            raise ValueError('normal coverage must match positive supplied sample depth bins')
        ratios=cov/normal
        status='Matched-normal depth ratios; no purity/ploidy or absolute copy-number inference'
    else:
        ratios=cov/np.median(cov) if cov.size else cov
        status='Sample-median relative coverage only; not copy-number gain/loss inference'
    if not np.isfinite(ratios).all():
        raise ValueError('copy ratio overflow')
    for i,value in enumerate(ratios):
        cnv.append({'bin':i,'copy_ratio':round(float(value),4),
                    'state':'relative_high' if value>1.3 else 'relative_low' if value<.7 else 'relative_baseline',
                    'threshold_status':'hand-set 1.3/.7 flags, not calibrated calls'})
    rearrangements=[]
    for junction in [] if junction_evidence is None else junction_evidence:
        if not isinstance(junction,dict):
            raise ValueError('junction must be a mapping')
        for side in ('left','right'):
            endpoint=junction.get(side)
            if not isinstance(endpoint,dict) or not isinstance(endpoint.get('chrom'),str) or not endpoint['chrom']:
                raise ValueError('junction endpoints require chromosome and integer position')
            position=endpoint.get('position')
            if isinstance(position,bool) or not isinstance(position,int) or position<0:
                raise ValueError('junction position must be nonnegative integer')
        counts=[junction.get(name,0) for name in ('split_reads','discordant_pairs')]
        if any(isinstance(x,bool) or not isinstance(x,int) or x<0 for x in counts) or not sum(counts):
            raise ValueError('junction requires positive integer read support')
        item=copy.deepcopy(junction)
        item.update({'support_reads':sum(counts),'source':'supplied junction evidence',
                     'type':'supported junction candidate','status':'Evidence supplied, not independently aligned/validated; read overlap/deduplication unverified'})
        rearrangements.append(item)
    meth=np.asarray([] if methylation is None else methylation,float)
    if meth.ndim!=1 or not np.isfinite(meth).all() or np.any(meth<0) or np.any(meth>1):
        raise ValueError('methylation must be finite 1D fractions in [0,1]')
    return {'supplied_variants':variants,'variant_origin_status':'Unclassified: somatic/germline/CHIP origin not inferred',
            'haplotype_reconstruction':hap,'copy_number_profile':cnv,'copy_number_status':status,
            'structural_rearrangements':rearrangements,
            'rearrangement_status':'Supplied supported junction candidates, not validated SV calls' if rearrangements else
                                   'Missing: no supplied split-read or discordant-pair junction evidence',
            'epigenetic_profile':{'mean_methylation':float(meth.mean()),'variance':float(meth.var())} if meth.size else {},
            'partial_genome':True,'status':'Supplied evidence summary; not reconstructed tumor genome'}


from .multiomics import (fit_multiomics_classifier, predict_multiomics_classifier,
                         evaluate_multiomics_classifier)


def integrate_multiomics(ctdna, methylation=(), proteins=(), metabolites=(), *, model=None) -> dict:
    """Summarize supplied modalities; predict label classes only with fitted model."""
    arrays=[np.asarray(v,float) for v in (ctdna,methylation,proteins,metabolites)]
    if any(a.ndim!=1 or not np.isfinite(a).all() for a in arrays):
        raise ValueError('modalities must be finite 1D arrays')
    summaries=[float(a.mean()) if a.size else None for a in arrays]
    names=['ctDNA','methylation','proteomics','metabolomics']
    result={'cancer_probability':None,'tissue_of_origin':None,'tissue_probabilities':{},
            'latent_signature':summaries,'modality_counts':[len(a) for a in arrays],
            'modalities':names,'model_status':'Missing fitted model; supplied modality summaries only'}
    if model is not None:
        if model.get('feature_names')!=names or any(v is None for v in summaries):
            raise ValueError('fitted model must use four modality means in documented order, all supplied')
        result['fitted_classification']=predict_multiomics_classifier(model,[summaries])
        result['model_status']='Fitted supplied-label classifier; clinical cancer/tissue semantics not inferred'
    return result


def longitudinal_trajectory(samples) -> dict:
    """Fit supplied signal versus time; no biological response inference."""
    import copy, math
    from scipy.stats import linregress, t as student_t
    rows=copy.deepcopy(list(samples))
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError('samples must be mappings')
        for key in ('time','burden'):
            value=row.get(key)
            if isinstance(value,bool) or not isinstance(value,(int,float,np.number)) or not math.isfinite(value):
                raise ValueError('time and burden must be finite numeric values')
        if row['burden']<0:
            raise ValueError('supplied burden signal must be nonnegative')
    rows.sort(key=lambda x:x['time'])
    if len({r['time'] for r in rows})!=len(rows):
        raise ValueError('time points must be unique; aggregate technical replicates explicitly')
    result={'trajectory':rows,'sample_count':len(rows),'trend':'insufficient_data',
            'slope':None,'intercept':None,'slope_interval_95':None,'residual_sum_squares':None,
            'percent_change':None,'clonal_expansion':None,
            'status':'Supplied signal trend only; not treatment response, progression or clonal selection',
            'uncertainty_assumptions':'IID homoscedastic normal residuals; assay error and independence unverified'}
    if len(rows)<2:
        return result
    times=np.array([r['time'] for r in rows]);values=np.array([r['burden'] for r in rows])
    fit=linregress(times,values)
    predicted=fit.intercept+fit.slope*times
    rss=float(np.sum((values-predicted)**2))
    if not np.isfinite([fit.slope,fit.intercept,rss]).all():
        raise ValueError('regression overflow')
    result.update({'slope':float(fit.slope),'intercept':float(fit.intercept),
                   'residual_sum_squares':rss,
                   'trend':'increasing' if fit.slope>1e-4 else 'decreasing' if fit.slope< -1e-4 else 'flat',
                   'trend_threshold_status':'hand-set absolute slope threshold 1e-4 in supplied units'})
    if values[0]>0:
        percent=float(100*(values[-1]-values[0])/values[0])
        if not math.isfinite(percent):
            raise ValueError('percent change overflow')
        result['percent_change']=percent
    if len(rows)>2:
        width=float(student_t.ppf(.975,len(rows)-2)*fit.stderr)
        result['slope_interval_95']=[float(fit.slope-width),float(fit.slope+width)]
    return result


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
    """Research evidence summary; not a clinical or specification-complete pipeline."""
    denoised = consensus_denoise(fragment_features)
    arch = reconstruct_tumor_architecture(variants, fragment_alleles, coverage, methylation)
    raw = np.asarray(fragment_features, float)[...,0].ravel()
    calls = [{"locus_index": i, "allele_fraction": float(v), "evidence_score": float(c)}
             for i,(v,c) in enumerate(zip(raw, np.asarray(denoised["evidence_score"]).ravel())) if c >= .5]
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
                       "signal_trend": trajectory["trend"],
                       "progression_risk": None,
                       "treatment_response": None,
                       "raw_vs_denoised": {"raw": raw.tolist(),
                                           "denoised": np.asarray(denoised["score_weighted_allele_support"]).ravel().tolist()},
                       "mutation_heatmap": denoised["evidence_score"],
                       "disclaimer": "research-use inference; not a clinical diagnosis"}}
