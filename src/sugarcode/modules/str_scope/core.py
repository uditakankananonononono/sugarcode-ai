from __future__ import annotations
import math
from collections import Counter
from ...bio.sequence import clean_dna


# Preferred reporting phases for known expansion motifs (either strand).
_PREFERRED_PHASES = ("CAG", "CTG", "CGG", "CCG", "GAA", "TTC", "GCC", "GGC", "CCTG", "CAGG", "GGGGCC", "GGCCCC")


def _canonical_unit(unit: str) -> str:
    """Lexicographically smallest cyclic rotation (strand-specific), for comparison."""
    return min(unit[i:] + unit[:i] for i in range(len(unit))) if unit else unit


def _phase_normalize(s: str, start: int, u: int) -> dict:
    """Resolve the reporting phase of a tandem repeat found at `start`.

    A greedy left-to-right scan can begin inside the flank when the flank's
    last bases match the unit's tail (GGG+CAGx10 is first seen as GCAx10).
    Take the maximal period-u span (s[j]==s[j+u]) and, among start offsets
    inside its first unit, keep those with the most whole units; prefer a
    known disease-motif phase (CAG over GCA/AGC), otherwise the leftmost.
    """
    span_end = start + u
    while span_end < len(s) and s[span_end] == s[span_end - u]:
        span_end += 1
    span_start = start
    while span_start > 0 and s[span_start - 1] == s[span_start - 1 + u]:
        span_start -= 1
    cands = []
    for k in range(u):
        st = span_start + k
        reps = (span_end - st) // u
        if reps >= 1:
            cands.append((reps, s[st:st + u] in _PREFERRED_PHASES, -st, st))
    reps, _, _, st = max(cands)
    unit = s[st:st + u]
    return {"start": st, "unit": unit, "unit_len": u, "repeats": reps, "length": reps * u,
            "canonical_unit": _canonical_unit(unit), "span_start": span_start, "span_end": span_end}


def _min_period(unit: str) -> int:
    n = len(unit)
    for p in range(1, n):
        if n % p == 0 and unit == unit[:p] * (n // p):
            return p
    return n


def find_strs(seq: str, min_unit: int = 1, max_unit: int = 6, min_repeats: int = 4) -> list[dict]:
    """Tandem-repeat detection over 1-6 bp units with phase normalization.

    Every maximal period-u run (s[j] == s[j+u]) is a candidate for each unit
    length; overlapping candidates are resolved longest-first (ties: shorter
    unit, then leftmost), so a short homopolymer inside the flank can no
    longer hide a longer compound repeat (GGGGTTx4 after a G-run was lost by
    the earlier greedy left-to-right scan). Each hit reports the unit in a
    stable phase (see _phase_normalize), a rotation-invariant canonical_unit,
    and the full periodic span including partial units at either edge.
    """
    import numpy as np
    s = clean_dna(seq)
    n = len(s)
    if n == 0:
        return []
    arr = np.frombuffer(s.encode("ascii"), dtype=np.uint8)
    cands = []
    for u in range(min_unit, max_unit + 1):
        if n < 2 * u:
            continue
        eq = (arr[:-u] == arr[u:]).astype(np.int8)
        d = np.diff(np.concatenate(([0], eq, [0])))
        starts = np.flatnonzero(d == 1)
        ends = np.flatnonzero(d == -1)  # exclusive end of the eq run
        keep = (ends - starts + u) >= min_repeats * u
        for j0, j1 in zip(starts[keep].tolist(), ends[keep].tolist()):
            unit = s[j0:j0 + u]
            if _min_period(unit) < u:
                continue  # homopolymers / lower-period runs are reported at their own period
            cand = _phase_normalize(s, j0, u)
            if cand["repeats"] >= min_repeats:
                cands.append(cand)
    cands.sort(key=lambda c: (-c["length"], c["unit_len"], c["start"]))
    taken = []
    hits = []
    def _free(lo, hi):
        return not any(lo < t_hi and t_lo < hi for t_lo, t_hi in taken)

    for c in cands:
        lo, hi = c["start"], c["start"] + c["length"]
        if not _free(lo, hi):
            # Try the other reporting phases inside the same periodic span
            # (TAx7 followed by CACAx7: the CA phase does not touch the TA run).
            u = c["unit_len"]
            alt = None
            for st in range(c["span_start"], c["span_start"] + u):
                reps = (c["span_end"] - st) // u
                if reps >= min_repeats and _free(st, st + reps * u) and (alt is None or reps > alt[0]):
                    alt = (reps, st)
            if alt is None:
                continue
            reps, st = alt
            unit = s[st:st + u]
            c = dict(c, start=st, unit=unit, repeats=reps, length=reps * u,
                     canonical_unit=_canonical_unit(unit))
            lo, hi = st, st + reps * u
        taken.append((lo, hi))
        hits.append(c)
    hits.sort(key=lambda c: c["start"])
    return hits


# Published allele bands (repeat units, inclusive upper bounds), GeneReviews:
# HTT CAG - NBK1305 table "methods to characterize HTT": normal <=26,
#   intermediate 27-35, reduced penetrance 36-39, full penetrance >=40.
# FMR1 CGG - NBK1384 table "types of FMR1 repeat expansion": premutation
#   ~55-200, full mutation >200 (alleles below 55 are not premutations).
LOCUS_BANDS = {
    "HTT": [(26, "normal range"), (35, "intermediate range"),
            (39, "reduced-penetrance pathogenic range"), (None, "full-penetrance pathogenic range")],
    "FMR1": [(54, "below premutation range"), (200, "premutation range"),
             (None, "full mutation range")],
}


def expansion_call(sample_repeats: int, reference_repeats: int, unit: str = "",
                   locus: str | None = None) -> dict:
    """Classify an STR genotype vs reference (normal/intermediate/expanded).

    With a locus that has published bands (LOCUS_BANDS), the class comes from
    those bands; the generic delta rule otherwise mislabels e.g. HTT 27-28 as
    normal and FMR1 premutations (55-200) as pathogenic full expansions.
    """
    delta = sample_repeats - reference_repeats
    bands = LOCUS_BANDS.get((locus or "").upper())
    if bands:
        cls = next(lbl for hi, lbl in bands if hi is None or sample_repeats <= hi)
    elif delta <= 2:
        cls = "normal range"
    elif delta <= 10:
        cls = "intermediate / premutation range"
    else:
        cls = "expanded - pathogenic-range candidate"
    out = {
        "unit": unit,
        "reference_repeats": reference_repeats,
        "sample_repeats": sample_repeats,
        "delta": delta,
        "classification": cls,
        "instability_risk": round(1 - math.exp(-max(delta, 0) / 12.0), 3),
    }
    if bands:
        out["locus"] = locus.upper()
    return out


# Normal-range upper bounds (repeat units) at canonical disease loci, used only
# when a locus carries no explicit 'delta' and no caller reference is given:
# HTT CAG 26, DMPK CTG 34, FMR1 CGG 44, FXN GAA 33, CNBP CCTG 26, C9orf72 GGGGCC 24.
# Loci whose motif matches none of these use DEFAULT_REFERENCE_REPEATS.
# Override per locus with reference_repeats (int, or {motif: repeats}).
REFERENCE_REPEATS = {"CAG": 26, "CTG": 34, "CGG": 44, "GAA": 33, "CCTG": 26, "GGGGCC": 24}
DEFAULT_REFERENCE_REPEATS = 10
_HOT_MOTIFS = ("CAG", "CTG", "CGG", "GCC", "GAA", "CAGG", "CCTG", "GGGGCC")
_COMP = str.maketrans("ACGT", "TGCA")


def _motif_class(unit: str) -> set[str]:
    """All cyclic rotations of a motif and of its reverse complement."""
    u = unit.upper()
    rc = u.translate(_COMP)[::-1]
    return {x[i:] + x[:i] for x in (u, rc) for i in range(len(x))}


def _reference_for(unit: str, reference_repeats=None) -> int:
    if isinstance(reference_repeats, (int, float)):
        return int(reference_repeats)
    cls = _motif_class(unit)
    table = dict(REFERENCE_REPEATS)
    if isinstance(reference_repeats, dict):
        table.update({k.upper(): v for k, v in reference_repeats.items()})
    for motif, ref in table.items():
        if motif in cls:
            return int(ref)
    return DEFAULT_REFERENCE_REPEATS


def diagnostic_index(str_loci: list[dict], repair_pathway_links: int = 0,
                     reference_repeats=None) -> dict:
    """Diagnostic potential index across loci.

    Combines expansion burden, motif pathogenicity priors (known expansion
    disease motifs, matched across rotations and reverse complement) and
    DNA-repair-pathway disruption links. Accepts expansion_call() records
    (which carry 'delta') or raw find_strs() hits (delta derived from
    'repeats' minus the motif reference; see REFERENCE_REPEATS).
    """
    hot = set().union(*(_motif_class(m) for m in _HOT_MOTIFS))
    score = 0.0
    annotated = []
    for locus in str_loci:
        unit = locus["unit"].upper()
        if "delta" in locus:
            delta, ref, source = locus["delta"], locus.get("reference_repeats"), "supplied"
        elif "repeats" in locus:
            ref = _reference_for(unit, reference_repeats)
            delta, source = locus["repeats"] - ref, "derived_from_reference"
        else:
            raise ValueError("each locus needs 'delta' or 'repeats'")
        is_hot = unit in hot
        w = 1.5 if is_hot else 1.0
        contrib = w * min(max(delta, 0) / 10.0, 3.0)
        score += contrib
        annotated.append({**locus, "hot_motif": is_hot, "delta": delta,
                          "reference_repeats": ref, "delta_source": source,
                          "contribution": round(contrib, 3)})
    score += 0.5 * repair_pathway_links
    index = round(1 - math.exp(-score / 5.0), 3)
    return {
        "diagnostic_potential_index": index,
        "loci": annotated,
        "repair_pathway_links": repair_pathway_links,
        "interpretation": ("high" if index > 0.6 else "moderate" if index > 0.3 else "low")
        + " diagnostic potential for repeat-instability disease",
    }

# Transparent single-molecule, stochastic repair and pathway models; no trained GNN.
import numpy as np

def reconstruct_repeat_reads(reads,motif):
    motif=clean_dna(motif); rows=[]
    for rid,read in enumerate(reads):
        s=clean_dna(read); best={'repeat_count':0,'start':None,'interruptions':[]}
        for frame in range(len(motif)):
            chunks=[s[i:i+len(motif)] for i in range(frame,len(s)-len(motif)+1,len(motif))]; runs=[]; start=0
            for i,c in enumerate(chunks+['END']):
                if c==motif or (len(c)==len(motif) and sum(a!=b for a,b in zip(c,motif))<=1): continue
                if i>start: runs.append((start,i,chunks[start:i]))
                start=i+1
            if runs:
                a,b,cs=max(runs,key=lambda x:x[1]-x[0]); ints=[{'repeat_index':j,'observed':c} for j,c in enumerate(cs) if c!=motif]
                if b-a>best['repeat_count']: best={'repeat_count':b-a,'start':frame+a*len(motif),'interruptions':ints}
        rows.append({'read_id':rid,**best,'purity':1-len(best['interruptions'])/max(1,best['repeat_count'])})
    counts=np.array([r['repeat_count'] for r in rows],float); return {'reads':rows,'molecule_count':len(rows),'median_repeats':float(np.median(counts)) if len(counts) else 0,'mosaicism_std':float(counts.std()) if len(counts) else 0}

def locus_architecture(sequence,motif,flank=20,max_mismatch=1):
    """Locus repeat architecture with interruption-tolerant tract extension.

    Seeds on the longest exact run of the motif, then extends in-frame over
    units with <= max_mismatch substitutions, trimming so the tract starts
    and ends on an exact unit. Reports purity and each interruption.
    """
    motif=clean_dna(motif); s=clean_dna(sequence); u=len(motif)
    empty={'motif':motif,'repeat_count':0,'purity':0.0,'interruptions':[],'left_flank':'','right_flank':''}
    if not u: raise ValueError('motif must be non-empty')
    best=(0,-1)  # (exact repeats, start); phase-locked to the motif, unlike find_strs' greedy scan
    for i0 in range(len(s)-u+1):
        if s[i0:i0+u]==motif and (i0<u or s[i0-u:i0]!=motif):
            r=1
            while s[i0+r*u:i0+(r+1)*u]==motif: r+=1
            if r>best[0]: best=(r,i0)
    if best[0]<2: return empty
    h={'repeats':best[0]}; start,end=best[1],best[1]+best[0]*u
    def ok(c): return len(c)==u and sum(x!=y for x,y in zip(c,motif))<=max_mismatch
    while end+u<=len(s) and ok(s[end:end+u]): end+=u
    while start-u>=0 and ok(s[start-u:start]): start-=u
    while end-start>u and s[end-u:end]!=motif: end-=u
    while end-start>u and s[start:start+u]!=motif: start+=u
    units=[s[i:i+u] for i in range(start,end,u)]
    ints=[{'repeat_index':j,'position':start+j*u,'observed':c,'expected':motif} for j,c in enumerate(units) if c!=motif]
    return {'start':start,'unit':motif,'unit_len':u,'repeats':len(units),'length':end-start,'motif':motif,'repeat_count':len(units),
            'pure_repeats':h['repeats'],'purity':1-len(ints)/len(units),'interruptions':ints,
            'left_flank':s[max(0,start-flank):start],'right_flank':s[end:end+flank]}

def repeat_instability(initial_repeats,divisions=50,slippage=.05,mmr=.8,ber=.5,seed=0,trajectories=500):
    if not 0<=min(slippage,mmr,ber)<=max(slippage,mmr,ber)<=1: raise ValueError('rates must be in [0,1]')
    rng=np.random.default_rng(seed); lengths=np.full(trajectories,int(initial_repeats)); history=[lengths.copy()]
    for _ in range(divisions):
        event=rng.random(trajectories)<slippage*(1+.01*np.maximum(lengths-20,0)); repair=rng.random(trajectories)<(.7*mmr+.3*ber); direction=np.where(rng.random(trajectories)<.65,1,-1); lengths=np.maximum(1,lengths+event*(~repair)*direction); history.append(lengths.copy())
    H=np.asarray(history); return {'mean_trajectory':H.mean(1).tolist(),'variance_trajectory':H.var(1).tolist(),'final_distribution':lengths.tolist(),'expansion_probability':float(np.mean(lengths>initial_repeats)),'contraction_probability':float(np.mean(lengths<initial_repeats))}

def molecular_consequence(motif,repeats,region='coding',accessibility=.5):
    if region=='coding': aggregation=min(1,max(0,repeats-20)/60) if motif in ('CAG','CAA') else .1*min(1,repeats/50); disorder=min(1,.3+repeats/100); return {'region':region,'poly_amino_acid_length':repeats,'aggregation_risk':aggregation,'phase_separation_risk':aggregation*disorder,'structural_disorder':disorder}
    gc=(motif.count('G')+motif.count('C'))/len(motif); stall=min(1,repeats/80*(.5+gc)); return {'region':region,'polymerase_stalling':stall,'chromatin_closure':min(1,stall*(1-accessibility+.5)),'rna_toxicity':min(1,repeats/100*(1+gc)),'splice_disruption':min(1,stall*.7)}

def repair_network(repeats,mmr=.8,ber=.5,hr=.7,checkpoint=.7):
    stress=min(1,max(0,repeats-20)/80); nodes={'repeat_stress':stress,'MMR':mmr,'BER':ber,'HR':hr,'checkpoint':checkpoint,'chromatin':1-stress*.4}; edges=[('repeat_stress','MMR'),('MMR','checkpoint'),('BER','HR'),('checkpoint','chromatin')]; instability=stress*(1-.35*mmr-.2*ber-.25*hr-.2*checkpoint); return {'nodes':nodes,'edges':[{'source':a,'target':b} for a,b in edges],'genomic_instability_index':max(0,instability),'intervention_points':sorted(('MMR','BER','HR','checkpoint'),key=lambda x:nodes[x])[:2]}

def intervention_assessment(repeats,strategy,offtarget_risk=.1):
    efficacy={'repeat_interruption':.45,'rna_targeting':.55,'repair_modulation':.3,'contraction_editing':.65}.get(strategy,.2); expected=max(0,repeats*(1-efficacy)); return {'strategy':strategy,'baseline_repeats':repeats,'expected_repeats_or_burden':expected,'efficacy_proxy':efficacy,'offtarget_risk':offtarget_risk,'net_benefit':efficacy-offtarget_risk,'status':'non-procedural comparative concept, not therapeutic guidance'}

def str_report(sequence,motif,reads=None,region='coding'):
    arch=locus_architecture(sequence,motif); n=arch['repeat_count']; return {'architecture':arch,'single_molecule':reconstruct_repeat_reads(reads,motif) if reads else None,'instability':repeat_instability(n or 1,divisions=20),'molecular_consequence':molecular_consequence(motif,n,region),'repair_network':repair_network(n),'interventions':[intervention_assessment(n,s) for s in ('repeat_interruption','rna_targeting','repair_modulation')],'model_status':'Transparent repeat parsing, stochastic repair and pathway equations; no trained transformer/GNN and not clinical guidance.'}

def str_diagnostics(report):
    """Flat numeric diagnostic panel (>=50 features) derived from str_report()."""
    a=report['architecture']; i=report['instability']; c=report['molecular_consequence']; n=report['repair_network']; sm=report['single_molecule']; iv=report['interventions']
    motif=a['motif']; n_rep=float(a['repeat_count']); ref=_reference_for(motif) if motif else DEFAULT_REFERENCE_REPEATS
    mt=np.asarray(i['mean_trajectory'],float); vt=np.asarray(i['variance_trajectory'],float); fd=np.asarray(i['final_distribution'],float)
    gc=(motif.count('G')+motif.count('C'))/len(motif) if motif else 0.0
    ints=a['interruptions']; pos=[x['repeat_index'] for x in ints]
    reads=sm['reads'] if sm else []; rc=np.asarray([r['repeat_count'] for r in reads],float) if reads else np.zeros(1)
    rp=np.asarray([r['purity'] for r in reads],float) if reads else np.zeros(1)
    cvals={k:float(v) for k,v in c.items() if isinstance(v,(int,float)) and not isinstance(v,bool)}
    nodes=n['nodes']; eff={x['strategy']:x for x in iv}; best=max(iv,key=lambda x:x['net_benefit'])
    d={'repeat_count':n_rep,'unit_length':float(len(motif)),'repeat_length':float(a.get('length',0)),'pure_repeats':float(a.get('pure_repeats',0)),
       'purity':float(a.get('purity',0)),'interruption_count':float(len(ints)),
       'first_interruption_index':float(min(pos)) if pos else -1.0,'last_interruption_index':float(max(pos)) if pos else -1.0,
       'longest_pure_run':float(max(np.diff([-1]+pos+[int(n_rep)])-1)) if n_rep else 0.0,
       'motif_gc_fraction':gc,'left_flank_gc':_gc(a.get('left_flank','')),'right_flank_gc':_gc(a.get('right_flank','')),
       'hot_motif':float(any(m in _motif_class(motif) for m in _HOT_MOTIFS)) if motif else 0.0,
       'reference_repeats':float(ref),'delta_vs_reference':n_rep-ref,'fold_over_reference':n_rep/ref if ref else 0.0,
       'expansion_call_risk':expansion_call(int(n_rep),ref,motif)['instability_risk'],
       'molecule_count':float(sm['molecule_count'] if sm else 0),'median_read_repeats':float(sm['median_repeats'] if sm else 0),
       'mosaicism_std':float(sm['mosaicism_std'] if sm else 0),'read_repeat_min':float(rc.min()),'read_repeat_max':float(rc.max()),
       'read_repeat_range':float(np.ptp(rc)),'read_mean_purity':float(rp.mean()),'read_min_purity':float(rp.min()),
       'reads_expanded_fraction':float(np.mean(rc>ref)) if reads else 0.0,
       'expansion_probability':i['expansion_probability'],'contraction_probability':i['contraction_probability'],
       'stable_probability':1-i['expansion_probability']-i['contraction_probability'],'final_mean':float(fd.mean()),
       'final_median':float(np.median(fd)),'final_p90':float(np.percentile(fd,90)),'final_max':float(fd.max()),'final_min':float(fd.min()),
       'final_variance':float(vt[-1]),'mean_drift':float(mt[-1]-mt[0]),'drift_per_division':float((mt[-1]-mt[0])/max(1,len(mt)-1)),
       'variance_growth_per_division':float((vt[-1]-vt[0])/max(1,len(vt)-1)),'crossing_reference_fraction':float(np.mean(fd>ref)),
       'instability_index':float(n['genomic_instability_index'])}
    d.update({f'consequence_{k}':v for k,v in cvals.items()})
    d['consequence_burden']=max(cvals.values()) if cvals else 0.0
    d.update({f'network_{k}':float(v) for k,v in nodes.items()})
    d['network_edge_count']=float(len(n['edges']))
    for k in ('repeat_interruption','rna_targeting','repair_modulation'):
        if k in eff: d[f'intervention_{k}_net_benefit']=float(eff[k]['net_benefit']); d[f'intervention_{k}_expected_repeats']=float(eff[k]['expected_repeats_or_burden'])
    d['best_intervention_net_benefit']=float(best['net_benefit'])
    return d


def _gc(seq):
    return (seq.count('G')+seq.count('C'))/len(seq) if seq else 0.0
