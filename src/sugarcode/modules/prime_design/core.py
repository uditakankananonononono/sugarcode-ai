from __future__ import annotations
from ...bio.sequence import clean_dna, reverse_complement, tm_wallace, gc_content
from ..crispr_opt.core import pam_sites, score_off_targets

PBS_RANGE = (10, 16)   # PBS lengths (nt) per Anzalone et al.; the published PBS/RTT boundary leaves a 16 nt flap on the spacer, so longer PBS needs genomic context this function does not receive
RTT_RANGE = (10, 20)   # reverse-transcriptase template lengths (nt)


def design_pegrna(spacer: str, edit_seq: str, pbs_len: int | None = None,
                  rtt_len: int | None = None) -> dict:
    """Build a pegRNA from a 20 nt spacer and the desired edited strand context.

    edit_seq: the desired post-edit sequence 3' of the nick on the edited
    strand (RT template content). The PBS anneals to the 3' flap of the
    nicked strand, i.e. the genomic sequence immediately 5' of the nick;
    with an NGG PAM the PBS/RTT boundary follows the convention of the
    published, experimentally validated pegRNAs (Anzalone et al. 2019 HEK3
    +1 CTT and RNF2 +5 G>T; Chow et al. 2021): the PBS is the reverse
    complement of spacer[16-pbs_len:16] and the RTT templates from spacer
    position 17 (1-based). PBS length is chosen by Wallace-Tm targeting
    ~30-34 C within 10-16 nt; RTT within 10-20 nt.
    """
    spacer = clean_dna(spacer)
    if len(spacer) != 20:
        raise ValueError("spacer must be 20 nt")
    edit_seq = clean_dna(edit_seq)
    rc_edit = reverse_complement(edit_seq)

    if pbs_len is None:
        best, best_d = PBS_RANGE[0], 1e9
        for L in range(PBS_RANGE[0], PBS_RANGE[1] + 1):
            cand = reverse_complement(spacer[16 - L:16])
            d = abs(tm_wallace(cand) - 32.0)
            if d < best_d:
                best, best_d = L, d
        pbs_len = best
    if not PBS_RANGE[0] <= pbs_len <= PBS_RANGE[1]:
        raise ValueError(f"PBS length must be {PBS_RANGE[0]}-{PBS_RANGE[1]} nt")
    rtt_len = rtt_len or min(RTT_RANGE[1], max(RTT_RANGE[0], len(edit_seq)))
    if not RTT_RANGE[0] <= rtt_len <= RTT_RANGE[1]:
        raise ValueError(f"RTT length must be {RTT_RANGE[0]}-{RTT_RANGE[1]} nt")

    pbs = reverse_complement(spacer[16 - pbs_len:16])
    rtt = rc_edit[:rtt_len]
    ext = rtt + pbs  # 3' extension, 5'->3'
    # first base of RTT should not be C (pairs with scaffold G -> mispriming)
    warns = []
    if rtt and rtt[0] == "C":
        warns.append("RTT 5' base is C: risk of scaffold-templated misincorporation; prefer alternate RTT length")
    if gc_content(pbs) < 0.3 or gc_content(pbs) > 0.7:
        warns.append("PBS GC outside 30-70%: annealing may be weak or non-specific")
    return {
        "spacer": spacer,
        "pbs": pbs, "pbs_length": pbs_len, "pbs_tm_c": round(tm_wallace(pbs), 1),
        "rt_template": rtt, "rtt_length": rtt_len,
        "pegrna_3p_extension": ext,
        "full_pegrna": spacer + "GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGC" + ext,
        "warnings": warns,
    }


def design_edit(target_region: str, edit: dict, background: str | None = None) -> dict:
    """Design a full prime edit for a point mutation / small indel.

    edit: {"type": "substitution"|"insertion"|"deletion", "position": int,
           "ref": str, "alt": str}
    Finds PAMs near the edit, designs pegRNAs on each strand, finds PE3
    nicking sgRNAs 40-120 nt on the opposite strand, runs off-target scans.
    """
    region = clean_dna(target_region)
    pos = edit["position"]
    if not 0 <= pos < len(region):
        raise ValueError("edit position outside target region")
    etype = edit["type"]
    ref = clean_dna(edit["ref"]) if edit.get("ref") else ""
    alt = clean_dna(edit["alt"]) if edit.get("alt") else ""
    if etype == "substitution" and region[pos:pos + len(ref)] != ref:
        raise ValueError("ref does not match target region at position")

    if etype == "substitution":
        edited = region[:pos] + alt + region[pos + len(ref):]
    elif etype == "insertion":
        edited = region[:pos] + alt + region[pos:]
    elif etype == "deletion":
        edited = region[:pos] + region[pos + len(ref):]
    else:
        raise ValueError(f"unknown edit type {etype!r}")

    designs = []
    for site in pam_sites(region, "NGG"):
        dist = abs(site["position"] - pos)
        if dist > 35:
            continue  # PAM too far from edit for efficient PE
        if site["strand"] == "+":
            g_start = site["position"] - 20
            if g_start < 0:
                continue
            spacer = region[g_start:site["position"]]
            # RT template = edited strand 3' of the nick; the PBS/RTT
            # boundary is 4 nt upstream of the PAM per the published convention
            nick = site["position"] - 4
            if pos < nick or pos - nick >= 20:
                continue  # edit outside the reverse-transcribed window
            rtt_source = edited[nick:nick + 20]
        else:
            g_start = site["position"] + 3
            if g_start + 20 > len(region):
                continue
            spacer = reverse_complement(region[g_start:g_start + 20])
            nick = site["position"] + 4
            if pos >= nick or nick - pos > 20:
                continue  # edit outside the reverse-transcribed window
            rtt_source = reverse_complement(edited[max(0, nick - 20):nick])
        try:
            peg = design_pegrna(spacer, rtt_source[:20] if len(rtt_source) >= 10 else rtt_source)
        except ValueError:
            continue
        peg["pam_strand"] = site["strand"]
        peg["pam_position"] = site["position"]
        peg["distance_to_edit"] = dist
        if background:
            peg["off_targets"] = score_off_targets(spacer, background, max_mismatches=3)[:5]
        designs.append(peg)

    designs.sort(key=lambda d: d["distance_to_edit"])
    nicking = []
    for site in pam_sites(region, "NGG"):
        if designs and site["strand"] != designs[0]["pam_strand"]:
            d = abs(site["position"] - designs[0]["pam_position"])
            if 40 <= d <= 120:
                nicking.append({"strand": site["strand"], "position": site["position"],
                                "distance_from_primary": d})
    return {
        "edit": edit, "edited_region": edited,
        "pegrna_designs": designs[:5],
        "nicking_sgrna_candidates": nicking[:5],
        "pe_system": "PE3" if nicking else "PE2",
        "predicted_outcome_distribution": _outcome_distribution(designs[0]) if designs else None,
    }


def _outcome_distribution(peg: dict) -> dict:
    """Simplified efficiency/purity estimate from PBS Tm and RTT length."""
    tm_score = max(0.0, 1.0 - abs(peg["pbs_tm_c"] - 32.0) / 10.0)
    len_score = 1.0 - 0.02 * abs(peg["rtt_length"] - 14)
    eff = round(0.45 * tm_score * len_score, 3)
    return {"intended_edit": eff, "partial_rt_readthrough": round(0.2 * (1 - tm_score), 3),
            "indel_byproducts": round(0.1 + 0.15 * (1 - len_score), 3),
            "unedited": round(max(0.0, 1 - eff - 0.2 * (1 - tm_score) - (0.1 + 0.15 * (1 - len_score))), 3)}

# Explicit biophysical and repair models. There is no trained sequence model
# and this module is not clinically validated.
import math
import json
import numpy as np

def pbs_thermodynamics(pbs,target_temperature_c=37,salt_mM=50):
    s=clean_dna(pbs)
    if not 8<=len(s)<=25 or salt_mM<=0: raise ValueError("PBS must be 8-25 nt and salt_mM positive")
    tm=tm_wallace(s)+16.6*math.log10(salt_mM/1000); gc=gc_content(s); dg=-1.7*(s.count('G')+s.count('C'))-1.0*(s.count('A')+s.count('T'))+3.4; anneal=1/(1+math.exp(-(tm-target_temperature_c)/4))
    return {"length":len(s),"gc_fraction":gc,"tm_c":tm,"delta_g_kcal_mol":dg,"annealing_probability":anneal,"temperature_c":target_temperature_c,"salt_mM":salt_mM}

def secondary_structure(sequence,min_stem=4):
    s=clean_dna(sequence); rc=reverse_complement(s); best=0
    for shift in range(-len(s)+min_stem,len(s)-min_stem+1):
        run=0
        for i,b in enumerate(s):
            j=i+shift; run=run+1 if 0<=j<len(s) and b==rc[j] else 0; best=max(best,run)
    return {"longest_stem":best,"paired_fraction":min(1,2*best/len(s)),"structure_penalty":min(1,best/10)}

def rt_processivity(rt_template,base_processivity=.96):
    s=clean_dna(rt_template)
    if not 0<base_processivity<=1: raise ValueError("base_processivity must be in (0,1]")
    gc=gc_content(s); homopolymer=max((j-i for i in range(len(s)) for j in range(i+1,len(s)+1) if len(set(s[i:j]))==1),default=1); pause_penalty=.03*max(0,homopolymer-3)+.2*abs(gc-.5); completion=base_processivity**len(s)*math.exp(-pause_penalty)
    return {"length":len(s),"gc_fraction":gc,"homopolymer_max":homopolymer,"pause_penalty":pause_penalty,"completion_probability":completion}

def flap_resolution(rt_template,homology_length=10,fen1_activity=.8):
    s=clean_dna(rt_template)
    if homology_length<1 or not 0<=fen1_activity<=1: raise ValueError("invalid flap parameters")
    equilibration=1-math.exp(-homology_length/8); structure=secondary_structure(s)['structure_penalty']; resolution=fen1_activity*equilibration*(1-.5*structure)
    return {"equilibration":equilibration,"structure_penalty":structure,"resolution_probability":resolution}

def repair_competition(rt_template,mmr_activity=.7,ber_activity=.2,fen1_activity=.8,nick_bias=.5):
    for v,n in ((mmr_activity,'mmr'),(ber_activity,'ber'),(fen1_activity,'fen1'),(nick_bias,'nick_bias')):
        if not 0<=v<=1: raise ValueError(f"{n} must be in [0,1]")
    completion=rt_processivity(rt_template)['completion_probability']; flap=flap_resolution(rt_template,fen1_activity=fen1_activity)['resolution_probability']; raw=np.array([completion*flap*(.4+.6*nick_bias),mmr_activity*(1-nick_bias)*.35,ber_activity*.15,(1-completion)*.5+.05]); raw=raw/raw.sum()
    return {"intended":float(raw[0]),"reverted":float(raw[1]),"partial_edit":float(raw[2]),"indel":float(raw[3]),"pathway_inputs":{"mmr":mmr_activity,"ber":ber_activity,"fen1":fen1_activity,"nick_bias":nick_bias}}

def nicking_strategy(primary_position,candidates,edited_strand='+'):
    ranked=[]
    for c in candidates:
        distance=abs(int(c['position'])-primary_position); orientation=1 if c.get('strand')!=edited_strand else .3; distance_score=math.exp(-((distance-70)/35)**2); dsb_risk=math.exp(-distance/15) if c.get('strand')!=edited_strand else .05; timing=1-math.exp(-distance/30); score=.5*distance_score+.3*orientation+.2*timing-.4*dsb_risk; ranked.append({**c,"distance":distance,"orientation_score":orientation,"timing_score":timing,"dsb_like_risk":dsb_risk,"score":score,"strategy":"PE3b" if c.get('requires_edit_match') else "PE3"})
    return sorted(ranked,key=lambda x:(-x['score'],x['distance']))

def spacer_binding_risk(spacer, background, max_mismatches=3, intended_position=None):
    """Scan spacer homologs with binding hazard highest for exact matches.

    ``score_off_targets`` exposes mismatch *dissimilarity* as ``risk``. Prime
    Design converts it back to similarity (1-dissimilarity). An exact hit is
    excluded only when its observed position equals ``intended_position``;
    other perfect copies remain maximum-hazard off-targets.
    """
    spacer = clean_dna(spacer)
    hits = score_off_targets(spacer, background, max_mismatches)
    ranked = []
    for hit in hits:
        if intended_position is not None and hit["position"] == intended_position and hit["mismatches"] == 0:
            continue
        binding_risk = max(0.0, min(1.0, 1.0 - float(hit["risk"])))
        ranked.append({**hit, "binding_risk": binding_risk})
    ranked.sort(key=lambda item: (-item["binding_risk"], item["mismatches"], item["position"]))
    return {"hit_count": len(ranked),
            "aggregate_binding_risk": float(sum(h["binding_risk"] for h in ranked)),
            "top_hits": ranked[:10],
            "intended_position_excluded": intended_position}

def rt_template_offtarget_risk(rt_template,background,min_identity=.7):
    r=clean_dna(rt_template); bg=clean_dna(background); hits=[]
    for i in range(len(bg)-len(r)+1):
        window=bg[i:i+len(r)]; identity=sum(a==b for a,b in zip(r,window))/len(r)
        if identity>=min_identity: hits.append({"position":i,"identity":identity,"annealing_probability":identity*pbs_thermodynamics(r[:min(17,len(r))])['annealing_probability']})
    hits.sort(key=lambda x:-x['annealing_probability']); return {"hit_count":len(hits),"aggregate_rewrite_risk":sum(h['annealing_probability'] for h in hits),"hits":hits[:10]}

def edit_window_score(edit_distance,rtt_length,optimal=(4,15)):
    if rtt_length<1 or edit_distance<0: raise ValueError("distance non-negative and RTT length positive")
    inside=optimal[0]<=edit_distance<=min(optimal[1],rtt_length); center=sum(optimal)/2; return {"inside_optimal_window":inside,"distance_score":math.exp(-((edit_distance-center)/5)**2),"partial_edit_risk":min(1,max(0,edit_distance-rtt_length+3)/5)}

def outcome_distribution(peg,repair=None,nick=None):
    repair=repair or repair_competition(peg['rt_template']); tm=max(0,1-abs(peg['pbs_tm_c']-32)/15); process=rt_processivity(peg['rt_template'])['completion_probability']; nick_gain=.15*(nick or {}).get('score',0); intended=min(1,repair['intended']*.5+.3*tm+.2*process+nick_gain); partial=repair['partial_edit']*(1-intended); indel=min(.5,repair['indel']+.2*(nick or {}).get('dsb_like_risk',0)); reverted=repair['reverted']; raw=np.array([intended,partial,indel,reverted,max(0,1-intended-partial-indel-reverted)]); raw=raw/raw.sum(); return {"intended_edit":float(raw[0]),"partial_edit":float(raw[1]),"indel":float(raw[2]),"reverted":float(raw[3]),"unedited":float(raw[4])}

def architecture_variants(spacer,edit_seq,pbs_lengths=range(10,17),rtt_lengths=range(10,21)):
    designs=[]
    for pbs in pbs_lengths:
        for rtt in rtt_lengths:
            if len(edit_seq)<max(pbs,rtt): continue
            peg=design_pegrna(spacer,edit_seq,pbs,rtt); thermo=pbs_thermodynamics(peg['pbs']); process=rt_processivity(peg['rt_template']); structure=secondary_structure(peg['pegrna_3p_extension']); repair=repair_competition(peg['rt_template']); efficiency=thermo['annealing_probability']*process['completion_probability']*(1-structure['structure_penalty']*.5); precision=outcome_distribution(peg,repair)['intended_edit']; designs.append({**peg,"predicted_efficiency":efficiency,"predicted_precision":precision,"thermodynamics":thermo,"processivity":process,"secondary_structure":structure,"repair":repair,"score":.55*efficiency+.45*precision})
    return sorted(designs,key=lambda x:(-x['score'],x['pbs_length'],x['rtt_length']))

def pegrna_diagnostics(peg,background=None):
    thermo=pbs_thermodynamics(peg['pbs']); rt=rt_processivity(peg['rt_template']); struct=secondary_structure(peg['pegrna_3p_extension']); flap=flap_resolution(peg['rt_template']); repair=repair_competition(peg['rt_template']); out=outcome_distribution(peg,repair)
    d={"spacer_gc":gc_content(peg['spacer']),"pbs_gc":gc_content(peg['pbs']),"rtt_gc":gc_content(peg['rt_template']),"pbs_length":float(peg['pbs_length']),"rtt_length":float(peg['rtt_length']),"extension_length":float(len(peg['pegrna_3p_extension'])),"pbs_tm_c":float(peg['pbs_tm_c']),"pbs_delta_g":thermo['delta_g_kcal_mol'],"pbs_annealing_probability":thermo['annealing_probability'],"rt_completion_probability":rt['completion_probability'],"rt_pause_penalty":rt['pause_penalty'],"rt_homopolymer_max":float(rt['homopolymer_max']),"structure_longest_stem":float(struct['longest_stem']),"structure_paired_fraction":struct['paired_fraction'],"structure_penalty":struct['structure_penalty'],"flap_equilibration":flap['equilibration'],"flap_resolution_probability":flap['resolution_probability'],"repair_intended":repair['intended'],"repair_reverted":repair['reverted'],"repair_partial":repair['partial_edit'],"repair_indel":repair['indel'],"outcome_intended":out['intended_edit'],"outcome_partial":out['partial_edit'],"outcome_indel":out['indel'],"outcome_reverted":out['reverted'],"outcome_unedited":out['unedited'],"warning_count":float(len(peg['warnings']))}
    if background is not None:
        spacing=spacer_binding_risk(peg['spacer'],background); rewrite=rt_template_offtarget_risk(peg['rt_template'],background); d.update({"background_spacer_hit_count":float(spacing['hit_count']),"background_spacer_binding_risk":float(spacing['aggregate_binding_risk']),"background_rt_hit_count":float(rewrite['hit_count']),"background_rt_rewrite_risk":float(rewrite['aggregate_rewrite_risk'])})
    return d

def export_design(design,format='json'):
    if format!='json': raise ValueError("only JSON export is supported")
    return json.dumps(design,sort_keys=True,separators=(',',':'))

def validation_strategy(edit_length,outcome=None):
    outcome=outcome or {}; expected=max(1e-4,float(outcome.get('intended_edit',.1))); depth=math.ceil(100/max(expected,.001)); return {"assay":"amplicon sequencing","minimum_read_depth":depth,"amplicon_span_bp":max(250,edit_length+200),"report":["intended allele fraction","partial RT alleles","indel spectrum","unedited fraction"],"orthogonal_confirmation":"independent sequencing chemistry for selected clones","model_status":"Planning guidance only; validate under institutional procedures."}

def compile_prime_edit(spacer,edit_seq,background=None,nicking_candidates=None):
    variants=architecture_variants(spacer,edit_seq)
    if not variants: raise ValueError("edit sequence must support requested PBS/RTT design ranges")
    top=variants[0]; nick=nicking_strategy(0,nicking_candidates or [])[:5]; selected_nick=nick[0] if nick else None; outcomes=outcome_distribution(top,top['repair'],selected_nick); diagnostics=pegrna_diagnostics(top,background)
    return {"recommended":top,"alternatives":variants[1:10],"nicking_strategies":nick,"outcome_distribution":outcomes,"diagnostics":diagnostics,"validation":validation_strategy(len(edit_seq),outcomes),"export":export_design({"spacer":top['spacer'],"pbs":top['pbs'],"rt_template":top['rt_template'],"outcomes":outcomes}),"model_status":"Explicit thermodynamic/repair surrogates; no trained sequence model and not clinically validated."}
