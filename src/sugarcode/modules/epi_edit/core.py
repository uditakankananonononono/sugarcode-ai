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
        # Polycomb-like closed CpG domains without active TF occupancy.
        if cpg >= 3 and tf_hits == 0 and accessibility < 0.45:
            marks.append("H3K27me3")
        # Gene-body proxy: tiles overlapping the supplied transcribed span.
        if promoter_span and i < promoter_span[1] and i + window > promoter_span[0] and gc >= 0.35:
            marks.append("H3K36me3")
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
        region = s[lo:hi] if hi > lo else s[max(0, a - 300):a + 100]
    else:
        lo, hi = max(0, a - 400), max(0, a - 50)
        # BUG 69: when the TSS sits too close to the sequence start for an
        # upstream window, the old fallback pulled guides from -300..+100,
        # i.e. inside the gene / the CRISPRi window, and reported
        # guide_window [0, 0]. CRISPRa now stays upstream-only; no room
        # upstream means no guides, reported honestly.
        region = s[lo:hi] if hi > lo else ""
    if region:
        designs = design_guides(region, background=background, top_n=5)
    else:
        designs = {"guides": []}
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

# Explicit chromatin/network dynamics; no trained model and not clinically validated.
import math, json
import numpy as np
from scipy.integrate import solve_ivp
EFFECTORS={"KRAB":{"accessibility":-.55,"acetylation":-.45,"methylation":.35},"VP64":{"accessibility":.4,"acetylation":.35,"methylation":-.1},"p300":{"accessibility":.5,"acetylation":.65,"methylation":-.1},"TET1":{"accessibility":.25,"acetylation":.1,"methylation":-.7},"DNMT3A":{"accessibility":-.35,"acetylation":-.15,"methylation":.75}}

def effector_response(effector,occupancy,baseline=None,cooperativity=2):
    if effector not in EFFECTORS: raise ValueError("unknown effector")
    if not 0<=occupancy<=1 or cooperativity<=0: raise ValueError("invalid occupancy/cooperativity")
    baseline={"accessibility":.5,"acetylation":.5,"methylation":.5,**(baseline or {})}; recruited=occupancy**cooperativity/(.5**cooperativity+occupancy**cooperativity); changes=EFFECTORS[effector]
    state={k:min(1,max(0,baseline[k]+recruited*changes[k])) for k in baseline}; expression=(state['accessibility']*.45+state['acetylation']*.4+(1-state['methylation'])*.15)
    return {"effector":effector,"recruited_fraction":recruited,"state":state,"relative_expression":expression}

def chromatin_graph(landscape,contacts=None):
    nodes=landscape['track']; n=len(nodes); edges=[]
    for i in range(n):
        for j in range(i+1,n):
            contact=float(contacts[i][j]) if contacts is not None else (1+abs(i-j))**-.8
            if contact>.15: edges.append({"source":i,"target":j,"contact":contact})
    return {"nodes":nodes,"edges":edges}

def spread_epigenetic_state(graph,seeds,mark='H3K27me3',steps=5,reader_writer=.6,decay=.15):
    n=len(graph['nodes']); state=np.zeros(n)
    for i,v in seeds.items(): state[int(i)]=float(v)
    adjacency=np.zeros((n,n))
    for e in graph['edges']: adjacency[e['source'],e['target']]=adjacency[e['target'],e['source']]=e['contact']
    rows=adjacency.sum(1,keepdims=True); norm=np.divide(adjacency,rows,out=np.zeros_like(adjacency),where=rows>0); history=[state.tolist()]
    for _ in range(steps): state=np.clip((1-decay)*state+reader_writer*norm@state,0,1); history.append(state.tolist())
    return {"mark":mark,"trajectory":history,"final":history[-1],"spread_distance_tiles":sum(x>.05 for x in state)}

def competitive_occupancy(dcas_concentration,kd,tf_concentration=0,tf_kd=1):
    if min(dcas_concentration,tf_concentration)<0 or min(kd,tf_kd)<=0: raise ValueError("invalid binding values")
    d=dcas_concentration/kd; t=tf_concentration/tf_kd; return {"dcas":d/(1+d+t),"endogenous_tf":t/(1+d+t),"unbound":1/(1+d+t)}

def expression_trajectory(effector,occupancy,hours=72,mrna_half_life=6,feedback=.1):
    target=effector_response(effector,occupancy)['relative_expression']; decay=math.log(2)/mrna_half_life
    def rhs(_t,y): return [target/(1+feedback*y[0])-decay*y[0]]
    t=np.linspace(0,hours,145); sol=solve_ivp(rhs,(0,hours),[1],t_eval=t,rtol=1e-8,atol=1e-9)
    # BUG 68: steady_state used to ignore the feedback term (target/decay),
    # overstating the true fixed point whenever feedback > 0.
    # Fixed point of target/(1+feedback*y) = decay*y:
    if feedback>0:
        steady=(-decay+math.sqrt(decay**2+4*decay*feedback*target))/(2*decay*feedback)
    else:
        steady=target/decay
    return {"time_h":sol.t.tolist(),"relative_expression":sol.y[0].tolist(),"steady_state":steady,"reversible":True}

def cell_state_effect(effector,occupancy,states):
    return {name:effector_response(effector,occupancy,state) for name,state in states.items()}

def regulatory_offtarget(hit,accessibility=.5,essential=False,enhancer=False):
    sequence=float(hit.get('cfd_score',hit.get('binding_probability',0))); consequence=1 if essential else .75 if enhancer else .4; return {"sequence_binding":sequence,"accessibility":accessibility,"functional_weight":consequence,"regulatory_risk":sequence*accessibility*consequence}

def multiplex_design(guides,max_guides=4,min_spacing=50):
    ranked=sorted(guides,key=lambda x:-x.get('composite',0)); chosen=[]
    for g in ranked:
        if all(abs(g.get('start',0)-x.get('start',0))>=min_spacing for x in chosen): chosen.append(g)
        if len(chosen)>=max_guides: break
    return {"selected":chosen,"count":len(chosen),"spacing_bp":min_spacing,"combined_occupancy":1-float(np.prod([1-g.get('composite',0) for g in chosen]))}

def epiedit_diagnostics(seq,effector='KRAB',occupancy=.7,transcribed_span=None):
    s=clean_dna(seq)
    # When no annotation is supplied, use the central half as an explicit gene-body proxy.
    # This keeps every declared mark reachable while callers can pass a real span.
    span=transcribed_span or (len(s)//4, max(len(s)//4 + 1, 3*len(s)//4))
    land=chromatin_landscape(s,span); track=land['track']; graph=chromatin_graph(land); response=effector_response(effector,occupancy); access=np.array([t['accessibility'] for t in track]); gc=np.array([t['gc'] for t in track]); motifs=np.array([t['tf_motifs'] for t in track],float)
    d={"length":float(land['length']),"tile_count":float(len(track)),"accessibility_mean":float(access.mean()),"accessibility_std":float(access.std()),"accessibility_min":float(access.min()),"accessibility_max":float(access.max()),"gc_mean":float(gc.mean()),"gc_std":float(gc.std()),"motif_mean":float(motifs.mean()),"motif_max":float(motifs.max()),"graph_nodes":float(len(graph['nodes'])),"graph_edges":float(len(graph['edges'])),"effector_occupancy":occupancy,"recruited_fraction":response['recruited_fraction'],"post_accessibility":response['state']['accessibility'],"post_acetylation":response['state']['acetylation'],"post_methylation":response['state']['methylation'],"relative_expression":response['relative_expression']}
    for mark in HISTONE_MARKS: d[f'mark_fraction.{mark}']=sum(mark in t['marks'] for t in track)/len(track)
    return d

def compile_epigenome_edit(seq,target_span,mode='CRISPRi',effector=None,cell_states=None,background=None):
    design=design_epigenome_edit(seq,target_span,mode,background); effector=effector or ('KRAB' if mode=='CRISPRi' else 'p300'); occ=design['guides'][0]['composite'] if design['guides'] else 0; graph=chromatin_graph(design['chromatin']); return {**design,"effector":effector,"effector_response":effector_response(effector,occ),"expression_trajectory":expression_trajectory(effector,occ),"domain_spread":spread_epigenetic_state(graph,{0:occ}) if graph['nodes'] else None,"cell_states":cell_state_effect(effector,occ,cell_states or {'target':{},'healthy':{'accessibility':.3}}),"multiplex":multiplex_design(design['guides']),"diagnostics":epiedit_diagnostics(seq,effector,occ),"vector_architecture":{"platform":"dCas9","effector":effector,"guide_count":min(4,len(design['guides'])),"status":"architecture only"},"validation":["CUT&RUN for effector-associated marks","ATAC-seq for accessibility","RNA-seq for target and network effects"],"model_status":"Transparent chromatin/network models; no trained model and not clinically validated."}
