from __future__ import annotations
import math
import numpy as np
from ..rna_nussinov.core import normalize_sequence, dot_bracket_to_pairs
from ...bio.sequence import clean_dna, find_motif, gc_content

# m6A installs at DRACH motifs (D=A/G/T, R=A/G, H=A/C/T); the central A is modified.
DRACH = "DRACH"
# HAND-SET positional priors (not trained or fitted here): m6A is reported to enrich near stop codons / 3' UTR
REGION_PRIORS = {"5utr": 0.35, "cds": 0.55, "near_stop": 0.85, "3utr": 0.75}


def _sequence(rna):
    return normalize_sequence(rna).replace('U', 'T')

def _bounds(s, start, end):
    a, b = _auto_cds(s)
    start = a if start is None else start
    end = b if end is None else end
    if (isinstance(start, bool) or isinstance(end, bool) or
        not isinstance(start, int) or not isinstance(end, int) or
        not 0 <= start <= end <= len(s)):
        raise ValueError('CDS bounds must be integer 0 <= start <= end <= sequence length')
    return start, end


def _fold_exposure(seq: str, pos: int, flank: int = 15) -> float:
    """Crude single-strandedness proxy: local GC in a flank around the site.
    m6A prefers exposed (AU-rich) loops."""
    s = seq[max(0, pos - flank):pos + flank + 1]
    return 1.0 - gc_content(s) if s else 0.5


def _auto_cds(s: str) -> tuple[int, int]:
    """First-ATG ORF heuristic: start codon to its in-frame stop. Falls back to the
    whole sequence when no ATG exists. This is not transcript annotation;
    supply verified CDS coordinates for region assignment."""
    i = s.find("ATG")
    if i < 0:
        return 0, len(s)
    for j in range(i, len(s) - 2, 3):
        if s[j:j + 3] in ("TAA", "TAG", "TGA"):
            return i, j
    return i, len(s)


def predict_m6a(rna: str, cds_start: int | None = None, cds_end: int | None = None,
                threshold: float = 0.5) -> list[dict]:
    """Rank DRACH candidates by an uncalibrated heuristic, not m6A probabilities.
    CDS bounds auto-detected from the first ATG when not supplied."""
    s = _sequence(rna)
    cds_start, cds_end = _bounds(s, cds_start, cds_end)
    if isinstance(threshold, bool) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('threshold must be finite and in [0, 1]')
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
                "heuristic_score": round(score, 3),
                "trained": False, "calibrated": False,
                "method": "DRACH regional-prior/local-GC heuristic",
            })
    return sorted(sites, key=lambda x: -x["heuristic_score"])


def modification_map(rna: str, cds_start: int | None = None, cds_end: int | None = None) -> dict:
    s = _sequence(rna)
    cds_start, cds_end = _bounds(s, cds_start, cds_end)
    sites = predict_m6a(s, cds_start, cds_end, threshold=0.0)
    return {
        "length": len(s),
        "drach_motifs": len(find_motif(s, DRACH)),
        "candidate_sites": [x for x in sites if x["heuristic_score"] >= 0.5],
        "track": [{"position": x["position"], "score": x["heuristic_score"]} for x in sites],
        "writer_eraser_reader": {
            "writers": ["METTL3", "METTL14", "WTAP"],
            "erasers": ["FTO", "ALKBH5"],
            "readers": ["YTHDF1", "YTHDF2", "YTHDC1"],
        },
    }


def optimize_mrna(rna: str, cds_start: int | None = None, cds_end: int | None = None) -> dict:
    """Return heuristic motif/GC suggestions, not a redesigned RNA or measured effects."""
    s = _sequence(rna)
    cds_start, cds_end = _bounds(s, cds_start, cds_end)
    sites = predict_m6a(s, cds_start, cds_end, threshold=0.0)
    edits = []
    for x in sites:
        if x["region"] == "CDS" and x["heuristic_score"] >= 0.6:
            edits.append({"action": "deoptimize_motif", "position": x["position"],
                          "rationale": "CDS m6A can slow ribosome transit; synonymously break DRACH motif"})
        elif x["region"] == "3'UTR" and 0.4 <= x["heuristic_score"] < 0.6:
            edits.append({"action": "retain_site", "position": x["position"],
                          "rationale": "retain candidate motif pending experimental reader/stability testing"})
    gc = gc_content(s[cds_start:cds_end])
    if gc < 0.45:
        edits.append({"action": "raise_cds_gc", "rationale": f"CDS GC {gc:.1%} low; target 50-60% for stability"})
    return {
        "current": modification_map(s, cds_start, cds_end),
        "proposed_edits": edits,
        "predicted_effect": {
            "translation_efficiency": None,
            "half_life": None,
            "status": "Missing: no measured or trained effect model; edits are motif/GC suggestions only",
        },
    }

# These are sequence patterns only, not universal biochemical site predictors.
MOD_MOTIFS = {'m6A': 'DRACH', 'm5C': 'CG', 'psi': 'TT', 'm1A': 'GATC'}

def nanopore_modification(signal, expected, noise_sd=.2):
    """Standardized residuals against a supplied matched control, not basecalling."""
    a, e = np.asarray(signal, float), np.asarray(expected, float)
    if (a.ndim != 1 or e.ndim != 1 or not a.size or a.shape != e.shape or
        not np.isfinite(a).all() or not np.isfinite(e).all() or
        isinstance(noise_sd, bool) or not math.isfinite(noise_sd) or noise_sd <= 0):
        raise ValueError('matched nonempty finite 1D signals and positive finite noise_sd required')
    with np.errstate(over='ignore'):
        z = (a-e)/noise_sd
    if not np.isfinite(z).all():
        raise ValueError('standardized residual overflow')
    return {'z_scores': z.tolist(), 'mean_absolute_z': float(np.abs(z).mean()),
            'status': 'Matched-control signal deviation only; no modification probabilities or trained basecaller'}

def multi_modification_map(rna):
    s = _sequence(rna)
    out = {}
    for name, motif in MOD_MOTIFS.items():
        if name == 'm6A':
            out[name] = sorted(predict_m6a(s), key=lambda x: x['position'])
        else:
            out[name] = [{'position': p, 'motif': s[p:p+len(motif)]}
                         for p in find_motif(s, motif)]
    return {'length': len(s), 'modifications': out, 'site_count': sum(map(len,out.values())),
            'status': 'Sequence motif candidates only; no measured modification calls. Non-m6A patterns are arbitrary search patterns, not validated site models.'}

def structure_ensemble(rna, window=None, temperature=37., max_length=2000):
    """Turner 2004 equilibrium ensemble via ViennaRNA. Full sequence by default.

    Explicit windows are independent folds: no cross-window pairs are possible.
    Requires the free optional ViennaRNA package. No fake-energy fallback.
    """
    s = normalize_sequence(rna)
    if window is not None and (isinstance(window, bool) or not isinstance(window, int) or window <= 0):
        raise ValueError('window must be a positive integer or None')
    if not math.isfinite(temperature) or not 0 <= temperature <= 100:
        raise ValueError('temperature must be finite in [0, 100] Celsius')
    if len(s) > max_length:
        raise ValueError('RNA exceeds max_length; use explicit windows or raise the limit consciously')
    from ..rna_nussinov.energy import _rna
    RNA = _rna()
    rows = []
    step = window or max(1, len(s))
    for start in range(0, len(s), step):
        seq = s[start:start+step]
        md = RNA.md(); md.temperature = float(temperature)
        fc = RNA.fold_compound(seq, md)
        db, mfe = fc.mfe(); fc.exp_params_rescale(mfe)
        _, ens = fc.pf(); bpp = fc.bpp()
        probs = [{'i': start+i-1, 'j': start+j-1, 'probability': float(bpp[i][j])}
                 for i in range(1,len(seq)+1) for j in range(i+1,len(seq)+1) if bpp[i][j] > 0]
        paired = [0.] * len(seq)
        for pair in probs:
            paired[pair['i']-start] += pair['probability']
            paired[pair['j']-start] += pair['probability']
        rows.append({'start': start, 'sequence': seq, 'dot_bracket': db,
                     'pairs': [[start+i,start+j] for i,j in dot_bracket_to_pairs(db)],
                     'mfe_kcal_mol': float(mfe), 'ensemble_free_energy_kcal_mol': float(ens),
                     'pair_probabilities': probs,
                     'unpaired_probabilities': [max(0.,1-p) for p in paired]})
    expected_paired = sum(2*sum(p['probability'] for p in w['pair_probabilities']) for w in rows)
    return {'windows': rows, 'mean_pairing': expected_paired/max(1,len(s)),
            'method': 'ViennaRNA Turner 2004 partition-function ensemble',
            'version': RNA.__version__, 'temperature_c': temperature,
            'scope': 'full sequence' if window is None else 'independent windows; cross-window pairs excluded',
            'status': 'Thermodynamic secondary-structure model, not experimental structure or modification prediction'}

def modification_kinetics(initial=.1, writer=1, eraser=.2, hours=24):
    params = (initial,writer,eraser,hours)
    if any(isinstance(x,bool) or not math.isfinite(x) for x in params) or not 0 <= initial <= 1 or min(writer,eraser,hours) < 0:
        raise ValueError('finite initial in [0,1] and nonnegative rates/time required')
    total = writer+eraser
    if not math.isfinite(total):
        raise ValueError('rate sum overflow')
    t = np.linspace(0,hours,121)
    equilibrium = writer/total if total else initial
    occ = equilibrium+(initial-equilibrium)*np.exp(-total*t)
    return {'time_h':t.tolist(), 'occupancy':occ.tolist(), 'equilibrium':equilibrium,
            'status':'Analytical two-state first-order kinetics with supplied rates, not fitted biology'}

def functional_impact(rna, modifications):
    return {'translation_efficiency_relative':None, 'immune_activation_relative':None,
            'stability_relative':None, 'structure':structure_ensemble(rna),
            'status':'Missing: no measured or trained functional-effect model; motif counts do not predict these effects'}

def design_rna(rna, delivery='LNP'):
    base = optimize_mrna(rna); mods = multi_modification_map(rna)
    return {**base, 'multi_modification_map':mods,
            'functional_impact':functional_impact(rna,mods['modifications']),
            'delivery':{'vehicle':delivery,'encapsulation_proxy':None,
                        'status':'Missing: no encapsulation model or measurements'},
            'validation':['matched-control direct RNA nanopore','miCLIP/MeRIP confirmation','ribosome profiling','innate immune panel'],
            'model_status':'Motif heuristics, real ViennaRNA thermodynamic ensemble and supplied-rate kinetics; no trained nanopore/transformer/GNN model or clinical validation.'}

def rna_diagnostics(r):
    m = r['multi_modification_map']; s = r['functional_impact']['structure']
    return {'length':float(m['length']), 'site_count':float(m['site_count']),
            **{name+'_count':float(len(m['modifications'][name])) for name in MOD_MOTIFS},
            'mean_pairing':s['mean_pairing'],
            'mfe_kcal_mol':sum(w['mfe_kcal_mol'] for w in s['windows']),
            'ensemble_free_energy_kcal_mol':sum(w['ensemble_free_energy_kcal_mol'] for w in s['windows'])}
