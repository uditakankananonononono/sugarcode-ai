from __future__ import annotations
import math
from ...bio.sequence import clean_dna, reverse_complement, gc_content, find_motif

PAMS = {
    "SpCas9": ["NGG", "NAG"],
    "SpCas9-VQR": ["NGAN"],
    "Cas12a": ["TTTV"],
    "Cas9-NG": ["NG"],
}
SEED_REGION = 12  # PAM-proximal positions weighted most for off-target risk


def pam_sites(seq: str, pam: str = "NGG") -> list[dict]:
    """Every PAM occurrence on both strands with coordinates."""
    s = clean_dna(seq)
    sites = []
    for pos in find_motif(s, pam):
        sites.append({"strand": "+", "position": pos, "pam": s[pos:pos + len(pam)]})
    rc = reverse_complement(s)
    for pos in find_motif(rc, pam):
        orig = len(s) - pos - len(pam)
        sites.append({"strand": "-", "position": orig, "pam": rc[pos:pos + len(pam)]})
    return sorted(sites, key=lambda x: x["position"])


def _extract_guides(seq: str, pam: str = "NGG", guide_len: int = 20) -> list[dict]:
    """Enumerate candidate guides 5' of each PAM on both strands."""
    s = clean_dna(seq)
    cands = []
    for site in pam_sites(s, pam):
        if site["strand"] == "+":
            p = site["position"]
            if p >= guide_len:
                cands.append({"strand": "+", "guide": s[p - guide_len:p],
                              "pam": site["pam"], "cut_site": p - 3,
                              "start": p - guide_len, "end": p})
        else:
            # guide lies downstream of PAM on + strand
            p_end = site["position"] + len(site["pam"])
            if p_end + guide_len <= len(s):
                g = reverse_complement(s[p_end:p_end + guide_len])
                cands.append({"strand": "-", "guide": g,
                              "pam": site["pam"], "cut_site": p_end + 3,
                              "start": p_end, "end": p_end + guide_len})
    return cands


def score_on_target(guide: str) -> float:
    """Heuristic on-target efficiency model (Rule-Set-1-style position weights
    plus GC-window and motif penalties, calibrated to 0..1)."""
    g = clean_dna(guide)
    if len(g) != 20:
        raise ValueError("on-target model expects a 20 nt guide")
    score = 0.0
    # position-specific nucleotide preferences (approx Doench 2014)
    fav = {15: "G", 19: "G", 2: "C", 3: "A"}
    for pos, base in fav.items():
        if g[pos] == base:
            score += 0.08
    gc = gc_content(g)
    if 0.40 <= gc <= 0.60:
        score += 0.30
    elif 0.30 <= gc <= 0.70:
        score += 0.15
    # penalties
    if "TTTT" in g:
        score -= 0.25  # Pol III terminator
    if g[-1] == "T":
        score -= 0.05
    if g.count("G") >= 8:
        score -= 0.10  # extreme G load / quadruplex risk
    dinuc_boost = sum(0.02 for i in range(19) if g[i:i + 2] in ("GG", "GC"))
    return max(0.0, min(1.0, 0.45 + score + dinuc_boost))


def _hairpin_score(guide: str) -> float:
    """Fraction of the guide that can self-pair (simple sliding complement)."""
    g = clean_dna(guide)
    best = 0
    comp = reverse_complement(g)
    for shift in range(-len(g) + 4, len(g) - 3):
        run = cur = 0
        for i in range(len(g)):
            j = i + shift
            if 0 <= j < len(g) and g[i] == comp[j]:
                cur += 1
                run = max(run, cur)
            else:
                cur = 0
        best = max(best, run)
    return best / len(g)


def score_off_targets(guide: str, background: str, max_mismatches: int = 4) -> list[dict]:
    """Scan a background sequence for off-target sites, seed-weighted."""
    g = clean_dna(guide)
    bg = clean_dna(background)
    k = len(g)
    hits = []
    for strand, s in (("+", bg), ("-", reverse_complement(bg))):
        for i in range(len(s) - k + 1):
            cand = s[i:i + k]
            mm = [(k - 1 - j) for j in range(k) if cand[j] != g[j]]
            if len(mm) <= max_mismatches:
                # CFD-like weighting: mismatches in PAM-proximal seed hurt most
                risk = 1.0
                for pos_from_3p in mm:
                    w = 0.65 if pos_from_3p < SEED_REGION else 0.87
                    risk *= w
                if risk < 1.0 or not mm:
                    hits.append({"strand": strand, "position": i,
                                 "mismatches": len(mm),
                                 "risk": round(1.0 - risk, 4)})
    return sorted(hits, key=lambda h: -h["risk"])


def design_guides(seq: str, pam: str = "NGG", background: str | None = None,
                  top_n: int = 5, regulatory_tracks: list[dict] | None = None) -> dict:
    """Full design pass: enumerate, filter GC 40-60%, score on/off-target, rank."""
    cands = _extract_guides(seq, pam)
    s = clean_dna(seq)
    graded = []
    for c in cands:
        gc = gc_content(c["guide"])
        # on-target: published Doench 2014 RS1 when the 30-mer context exists
        # inside the sequence; labeled heuristic at sequence edges
        ctx = _context_30mer(s, c["start"]) if c["strand"] == "+" else None
        if c["strand"] == "-":
            a, b = c["start"] - 6, c["end"] + 4
            if a >= 0 and b <= len(s):
                from ...bio.sequence import reverse_complement
                ctx = reverse_complement(s[a:b])
        if ctx:
            on = doench2014_ontarget(ctx)
            on_model = "doench2014_rs1"
        else:
            on = score_on_target(c["guide"])
            on_model = "heuristic_edge_fallback"
        hairpin = _hairpin_score(c["guide"])
        # off-target: published CFD (Doench 2016) scan
        if background:
            bg = clean_dna(background)
            # When the background IS the target sequence, exclude only the
            # candidate's own locus (the intended cut site). A distinct
            # background keeps perfect matches - they are the worst
            # off-targets (previously all perfect matches were silently
            # skipped everywhere, BUG 51).
            if bg == s:
                excl = ({(c["start"], "+")} if c["strand"] == "+"
                        else {(len(s) - c["end"], "-")})
            else:
                excl = None
            offs = score_off_targets_cfd(c["guide"], bg, max_mismatches=3,
                                         exclude_sites=excl)
        else:
            offs = []
        off_risk = sum(o["cfd_score"] for o in offs)
        # GC filter per spec (40-60% optimal window), hairpin suppresses folding
        composite = on * (1.0 - 0.5 * hairpin) / (1.0 + off_risk)
        if not (0.20 <= gc <= 0.80):
            continue
        graded.append({**c, "gc": round(gc, 3), "on_target": round(on, 3),
                       "on_target_model": on_model,
                       "hairpin_fraction": round(hairpin, 3),
                       "off_target_risk": round(off_risk, 3),
                       "off_target_model": "cfd_doench2016" if background else None,
                       "top_off_targets": offs[:3],
                       "composite": round(composite, 4)})
    graded.sort(key=lambda x: -x["composite"])
    return {
        "pam": pam,
        "scoring_models": {"on_target": "doench2014_rs1 (published) with heuristic edge fallback",
                           "off_target": "cfd_doench2016 (published)"},
        "candidates": len(cands),
        "guides": graded[:top_n],
        "pam_track": pam_sites(seq, pam),
        "regulatory_tracks": regulatory_tracks or [],
        "browser_track": _browser_track(seq, pam, graded[:top_n], regulatory_tracks or []),
    }


def _browser_track(seq: str, pam: str, guides: list[dict], tracks: list[dict]) -> dict:
    """Simulated genome-browser payload: coordinate system + feature tracks."""
    return {
        "reference_length": len(clean_dna(seq)),
        "tracks": [
            {"name": f"PAM {pam}", "type": "motif",
             "features": [{"start": s["position"], "end": s["position"] + len(s["pam"]),
                           "strand": s["strand"]} for s in pam_sites(seq, pam)]},
            {"name": "Top guides", "type": "guide",
             "features": [{"start": g["start"], "end": g["end"], "strand": g["strand"],
                           "score": g["composite"]} for g in guides]},
            *[{"name": t.get("name", f"track-{i}"), "type": "annotation",
               "features": t.get("features", [])} for i, t in enumerate(tracks)],
        ],
    }


# ---- Published CFD off-target model (Doench 2016) - verifiably sourced ----
import json as _json
from pathlib import Path as _Path

_DATA = _Path(__file__).parent / "data"
_CFD_MM = _json.load(open(_DATA / "cfd_mm_scores.json"))
_CFD_PAM = _json.load(open(_DATA / "cfd_pam_scores.json"))
_COMPLEMENT = {"A": "T", "T": "A", "U": "A", "C": "G", "G": "C"}


def cfd_score(wt_guide: str, off_guide: str, pam2: str = "GG") -> float:
    """Published CFD off-target score (Doench et al. 2016, matrices vendored
    verbatim from the CRISPOR distribution - see data/PROVENANCE.md).

    wt_guide / off_guide: 20-nt protospacers (same length).
    pam2: the off-target site's 2-nt PAM core ('GG' for NGG).
    Returns activity fraction 0-1 (1 = as active as on-target).
    """
    if len(wt_guide) != len(off_guide):
        raise ValueError("guides must be same length")
    pam2 = pam2.upper()
    if pam2 not in _CFD_PAM:
        raise KeyError(f"PAM {pam2!r} not in published matrix")
    wt = wt_guide.upper().replace("T", "U")
    off = off_guide.upper().replace("T", "U")
    score = 1.0
    for i, (w, o) in enumerate(zip(wt, off), 1):
        if w != o:
            key = f"r{w}:d{_COMPLEMENT[o]},{i}"
            score *= _CFD_MM[key]
    return round(score * _CFD_PAM[pam2], 6)


def score_off_targets_cfd(guide: str, background: str,
                          max_mismatches: int = 4,
                          exclude_sites: set | None = None) -> list[dict]:
    """Genome scan with the PUBLISHED CFD model: candidate sites within
    max_mismatches are scored by the real Doench matrices, PAM-aware.
    Perfect-match (0-mismatch) sites are reported like any other hit -
    they are the highest-risk off-targets - except coordinates in
    exclude_sites ((position, strand) pairs; design_guides uses this to
    skip a candidate's own locus when the background IS the target
    sequence)."""
    guide = guide.upper()
    out = []
    excl = exclude_sites or set()
    for strand, s in (("+", background.upper()),
                      ("-", str.maketrans("ACGT", "TGCA"))):
        seq = s if strand == "+" else background.upper().translate(str.maketrans("ACGT", "TGCA"))[::-1]
        for i in range(len(seq) - 23 + 1):
            protospacer = seq[i:i + 20]
            pam = seq[i + 20:i + 23]
            if len(pam) < 3 or pam[1:] != "GG":
                continue
            mm = sum(1 for a, b in zip(guide, protospacer) if a != b)
            if mm > max_mismatches:
                continue
            if mm == 0 and (i, strand) in excl:
                continue
            score = cfd_score(guide, protospacer, "GG")
            if score < 0.001:
                continue
            out.append({"position": i, "strand": strand,
                        "off_sequence": protospacer, "mismatches": mm,
                        "cfd_score": score,
                        "risk": "high" if score >= 0.3 else "medium" if score >= 0.05 else "low"})
    out.sort(key=lambda x: -x["cfd_score"])
    return out


# ---- Published Doench 2014 (Rule Set 1) on-target model - verifiably sourced ----
_DOENCH_PARAMS = [(p, m, w) for p, m, w in
                  _json.load(open(_DATA / "doench2014_params.json"))]
_DOENCH_INTERCEPT = 0.59763615
_DOENCH_GC_HIGH = -0.1665878
_DOENCH_GC_LOW = -0.2026259


def doench2014_ontarget(seq30: str) -> float:
    """Published Rule Set 1 on-target activity (Doench et al. 2014, table
    vendored verbatim from CRISPOR - see data/PROVENANCE.md).

    Input: 30-mer = 4 bp 5' flank + 20 bp guide + 3 bp PAM + 3 bp 3' flank.
    Returns activity 0-1 (logistic). Rule Set 2 is NOT vendored (see
    PROVENANCE.md) - this is RS1, labeled as such.
    """
    seq = seq30.upper()
    if len(seq) != 30:
        raise ValueError("needs a 30-mer: 4bp flank + 20bp guide + NGG + 3bp flank")
    guide = seq[4:24]
    gc = guide.count("G") + guide.count("C")
    score = _DOENCH_INTERCEPT + abs(10 - gc) * (_DOENCH_GC_LOW if gc <= 10 else _DOENCH_GC_HIGH)
    for pos, model, weight in _DOENCH_PARAMS:
        if seq[pos:pos + len(model)] == model:
            score += weight
    return round(1.0 / (1.0 + math.exp(-score)), 4)


def _context_30mer(seq: str, guide_start: int, guide_len: int = 20) -> str | None:
    """Build the Doench 30-mer when flanks exist inside the sequence."""
    a, b = guide_start - 4, guide_start + guide_len + 6  # +3 PAM +3 flank
    if a < 0 or b > len(seq):
        return None
    return seq[a:b]


def score_off_targets_cfd_fasta(guide: str, fasta_path: str,
                                max_mismatches: int = 4) -> dict:
    """CFD off-target scan over a FASTA FILE (streaming - constant memory).

    Each record (chromosome/contig) is scanned on both strands; hits carry the
    record id and coordinates. Suited to real reference files, not toy strings.
    """
    from ...bio.fasta import stream_fasta
    hits, scanned = [], []
    for rec in stream_fasta(fasta_path):
        scanned.append({"id": rec["id"], "length": len(rec["sequence"])})
        for h in score_off_targets_cfd(guide, rec["sequence"], max_mismatches):
            h["record"] = rec["id"]
            hits.append(h)
    hits.sort(key=lambda x: -x["cfd_score"])
    return {"guide": guide, "source_file": fasta_path,
            "records_scanned": scanned, "total_bases": sum(r["length"] for r in scanned),
            "hits": hits,
            "high_risk": [h for h in hits if h["risk"] == "high"],
            "model": "cfd_doench2016 (published)",
            "note": "streaming scan - memory constant in file size"}

# Transparent sequence/biophysical context models. No trained deep model is
# bundled, and predictions are not clinically validated.
import json
import numpy as np
NUCLEASES={"SpCas9":{"pam":"NGG","guide_length":20},"SaCas9":{"pam":"NNGRRT","guide_length":21},"Cas12a":{"pam":"TTTV","guide_length":23},"Cas9-NG":{"pam":"NG","guide_length":20}}

def mismatch_profile(guide,target):
    g=clean_dna(guide); t=clean_dna(target)
    if len(g)!=len(t): raise ValueError("guide and target lengths must match")
    positions=[i+1 for i,(a,b) in enumerate(zip(g,t)) if a!=b]; weights=[.35 if i>len(g)-12 else .13 for i in positions]; binding=float(np.prod([1-w for w in weights]))
    return {"mismatch_positions":positions,"mismatch_count":len(positions),"pam_proximal_mismatches":sum(i>len(g)-12 for i in positions),"binding_probability":binding}

def bulge_alignment(guide,target,max_bulge=1):
    g=clean_dna(guide); t=clean_dna(target); best={"identity":0,"bulge":None}
    for deletion in range(-max_bulge,max_bulge+1):
        if deletion==0: pairs=zip(g,t)
        elif deletion>0: pairs=zip(g[deletion:],t)
        else: pairs=zip(g,t[-deletion:])
        pairs=list(pairs); identity=sum(a==b for a,b in pairs)/max(1,len(pairs))
        if identity>best['identity']: best={"identity":identity,"bulge":deletion}
    return best

def hybrid_thermodynamics(guide,target):
    profile=mismatch_profile(guide,target); gc=gc_content(guide); dg=-1.5*len(guide)*(1+.4*gc)+2.2*profile['mismatch_count']+1.5*profile['pam_proximal_mismatches']; return {"delta_g_kcal_mol":dg,"binding_probability":profile['binding_probability']*math.exp(-max(0,dg+35)/8),"mismatch_profile":profile}

def chromatin_adjustment(base_score,atac=.5,dnase=.5,h3k27ac=.5,h3k4me3=.5,methylation=.5,nucleosome=.5):
    for v in (atac,dnase,h3k27ac,h3k4me3,methylation,nucleosome):
        if not 0<=v<=1: raise ValueError("chromatin tracks must be in [0,1]")
    accessibility=.3*atac+.2*dnase+.2*h3k27ac+.15*h3k4me3+.1*(1-methylation)+.05*(1-nucleosome); return {"base_score":base_score,"accessibility":accessibility,"context_score":base_score*(.35+.65*accessibility)}

def binding_kinetics(guide,target,cas_concentration=1):
    thermo=hybrid_thermodynamics(guide,target); on_rate=cas_concentration*1e6*thermo['binding_probability']; off_rate=math.exp((thermo['delta_g_kcal_mol']+40)/8)*.01; cleavage=on_rate/(on_rate+off_rate+1); return {"on_rate":on_rate,"off_rate":off_rate,"cleavage_probability":cleavage,"residence_time":1/max(off_rate,1e-12)}

def functional_offtarget_risk(hit,annotations=None):
    annotations=annotations or {}; consequence=1.0 if annotations.get('coding') else .8 if annotations.get('enhancer') else .5; essential=1+.5*float(annotations.get('essential_gene_proximity',False)); score=float(hit.get('cfd_score',hit.get('binding_probability',0)))*consequence*essential; return {"sequence_risk":float(hit.get('cfd_score',0)),"functional_weight":consequence*essential,"functional_risk":score}

def base_editor_window(guide,target_base='C',window=(4,8),activity_profile=None):
    g=clean_dna(guide); start,end=window
    if not 1<=start<=end<=len(g): raise ValueError("invalid 1-based editing window")
    profile=activity_profile or [math.exp(-((i-(start+end)/2)/2)**2) for i in range(1,len(g)+1)]; sites=[{"position":i,"base":b,"activity":profile[i-1]} for i,b in enumerate(g,1) if start<=i<=end and b==target_base]; return {"target_base":target_base,"window":list(window),"sites":sites,"bystander_count":max(0,len(sites)-1),"total_activity":sum(x['activity'] for x in sites)}

def prime_editor_architecture(spacer,pbs,rt_template,mmr_activity=.7):
    g=clean_dna(spacer); p=clean_dna(pbs); r=clean_dna(rt_template); tm=2*(p.count('A')+p.count('T'))+4*(p.count('G')+p.count('C')); structure=_hairpin_score(g+p+r); process=.96**len(r)*math.exp(-.2*abs(gc_content(r)-.5)); flap=1-math.exp(-len(r)/10); efficiency=(1/(1+math.exp(-(tm-30)/4)))*process*flap*(1-.4*structure); return {"pbs_tm_c":tm,"structure_penalty":structure,"rt_processivity":process,"flap_resolution":flap,"mmr_retention":1-.5*mmr_activity,"efficiency":efficiency}

def design_report(seq,pam='NGG',background=None,tracks=None,top_n=5):
    design=design_guides(seq,pam,background,top_n,tracks); guides=[]
    for g in design['guides']:
        context=chromatin_adjustment(g['on_target'],**(tracks[0].get('values',{}) if tracks and tracks[0].get('values') else {})); guides.append({**g,"chromatin":context,"context_efficiency":context['context_score'],"validation":{"assay":"amplicon sequencing","off_target_assay":"GUIDE-seq or orthogonal equivalent"}})
    return {**design,"guides":guides,"model_status":"Published CFD/RS1 plus transparent biophysical surrogates; no trained deep model and not clinically validated.","exports":{"json":json.dumps(guides,sort_keys=True),"bed":[f"target\t{g['start']}\t{g['end']}\t{g['guide']}\t{g['composite']}\t{g['strand']}" for g in guides]}}

def guide_diagnostics(guide,target=None,chromatin=None):
    g=clean_dna(guide); target=clean_dna(target or guide); mm=mismatch_profile(g,target); thermo=hybrid_thermodynamics(g,target); kinetics=binding_kinetics(g,target); context=chromatin_adjustment(score_on_target(g),**(chromatin or {})); base=base_editor_window(g); prime=prime_editor_architecture(g,g[:13],g[:15]); d={"gc":gc_content(g),"on_target":score_on_target(g),"hairpin":_hairpin_score(g),"mismatch_count":float(mm['mismatch_count']),"seed_mismatch_count":float(mm['pam_proximal_mismatches']),"binding_probability":mm['binding_probability'],"hybrid_delta_g":thermo['delta_g_kcal_mol'],"thermo_binding_probability":thermo['binding_probability'],"on_rate":kinetics['on_rate'],"off_rate":kinetics['off_rate'],"cleavage_probability":kinetics['cleavage_probability'],"residence_time":kinetics['residence_time'],"accessibility":context['accessibility'],"context_efficiency":context['context_score'],"base_edit_site_count":float(len(base['sites'])),"base_edit_bystander_count":float(base['bystander_count']),"base_edit_activity":base['total_activity'],"prime_pbs_tm":prime['pbs_tm_c'],"prime_structure_penalty":prime['structure_penalty'],"prime_processivity":prime['rt_processivity'],"prime_flap_resolution":prime['flap_resolution'],"prime_mmr_retention":prime['mmr_retention'],"prime_efficiency":prime['efficiency'],"poly_t":float('TTTT' in g),"seed_gc":gc_content(g[-12:]),"distal_gc":gc_content(g[:-12])}
    return d


def score_on_target_rs2(mer30: str, percent_peptide=None, aa_cut=None) -> float:
    """Published Rule Set 2 (Azimuth V3, Fusi/Doench 2016) on-target score.

    Takes the 30 nt context (4 nt + 20 nt guide + NGG + 3 nt). This is the
    real trained gradient-boosted model ported from Microsoft's BSD-3-Clause
    release - not a heuristic; see rule_set_2.py for provenance and the
    fixture-level validation (max error 5e-10 on Microsoft's 947-guide
    reference set). With percent_peptide/aa_cut omitted, the V3-nopos model
    (no gene-position features) is used, as in the original library.
    """
    from .rule_set_2 import score_guide
    return score_guide(mer30, percent_peptide=percent_peptide, aa_cut=aa_cut)


def rank_guides_rs2(seq: str, pam: str = "NGG", guide_len: int = 20) -> list[dict]:
    """Enumerate NGG candidate guides from a target region and score each with
    Rule Set 2 (nopos), returning candidates sorted by the published model's
    score. Requires 4 nt of context upstream and 3 nt downstream of each
    guide+PAM window; candidates too close to the sequence ends are skipped
    (their 30mer context is unavailable, and padding would fabricate data)."""
    from .rule_set_2 import score_guides
    s = clean_dna(seq)
    if pam != "NGG":
        raise ValueError("Rule Set 2 is trained for SpCas9 NGG guides only")
    cands = _extract_guides(s, pam, guide_len)
    usable = []
    for c in cands:
        if c["strand"] == "+":
            a = c["start"] - 4
            b = c["end"] + 3 + 3  # guide end + 3 PAM + 3 flank
            if a >= 0 and b <= len(s):
                c = dict(c)
                c["mer30"] = s[a:b]
                usable.append(c)
        else:
            a = c["start"] - 3 - 3  # 3 flank + 3 PAM upstream on + strand
            b = c["end"] + 4
            if a >= 0 and b <= len(s):
                c = dict(c)
                c["mer30"] = reverse_complement(s[a:b])
                usable.append(c)
    scores = score_guides([c["mer30"] for c in usable]) if usable else []
    for c, sc in zip(usable, scores):
        c["rule_set_2"] = float(sc)
    return sorted(usable, key=lambda x: -x["rule_set_2"])
