from __future__ import annotations
from ...bio.sequence import clean_dna, find_motif, gc_content, orfs
from ...bio import pwm

TF_MOTIFS = {
    "AP-1": "TGACTCA", "NF-kB": "GGGRNTTTCC", "p53": "RRRCWWGYYY",
    "TATA-box": "TATAWAW", "E-box": "CANNTG", "GC-box": "GGGCGG",
    "CCAAT": "CCAAT", "HNF4": "RGGTCAAAGGTCA",
}


def _cpg_islands(s: str, window: int = 200) -> list[dict]:
    islands = []
    for i in range(0, len(s) - window + 1, window // 2):
        w = s[i:i + window]
        gc = gc_content(w)
        cpg = w.count("CG")
        g = w.count("G")
        oe = (cpg * len(w)) / max(1, (w.count("C") * g)) if g else 0
        if gc > 0.5 and oe > 0.6:
            islands.append({"start": i, "end": i + window,
                            "gc": round(gc, 3), "cpg_obs_exp": round(oe, 3)})
    # merge overlapping
    merged = []
    for isl in islands:
        if merged and isl["start"] <= merged[-1]["end"]:
            merged[-1]["end"] = isl["end"]
        else:
            merged.append(dict(isl))
    return merged


def decode(seq: str, coding_spans: list[tuple[int, int]] | None = None) -> dict:
    """Decode the regulatory landscape of a (mostly non-coding) locus."""
    s = clean_dna(seq)
    coding_spans = coding_spans or []

    def noncoding(pos: int) -> bool:
        return not any(a <= pos < b for a, b in coding_spans)

    enhancers = []
    for name, motif in TF_MOTIFS.items():
        for pos in find_motif(s, motif):
            if noncoding(pos):
                enhancers.append({"tf": name, "position": pos,
                                  "motif": s[pos:pos + len(motif)]})
    # enhancer clusters: >=3 TF hits within 500 bp
    enhancers.sort(key=lambda e: e["position"])
    clusters = []
    for e in enhancers:
        if clusters and e["position"] - clusters[-1]["end"] < 500:
            clusters[-1]["hits"].append(e)
            clusters[-1]["end"] = e["position"]
        else:
            clusters.append({"start": e["position"], "end": e["position"], "hits": [e]})
    enh_clusters = [c for c in clusters if len(c["hits"]) >= 3]

    nc_orfs = [o for o in orfs(s, min_aa=20) if noncoding(o["start"])]
    lnc_candidates = [{"start": o["start"], "end": o["end"], "strand": o["strand"]}
                      for o in nc_orfs if o["aa_length"] < 100]

    formatted_clusters = [
        {"start": c["start"], "end": c["end"], "n_motifs": len(c["hits"]),
         "tfs": sorted({h["tf"] for h in c["hits"]})} for c in enh_clusters
    ]
    return {
        "length": len(s),
        "gc_content": round(gc_content(s), 4),
        "tf_motif_hits": enhancers,
        "enhancer_clusters": formatted_clusters,
        "cpg_islands": _cpg_islands(s),
        "lncrna_candidates": lnc_candidates,
        "dark_matter_fraction": round(1 - sum(b - a for a, b in coding_spans) / len(s), 4)
        if coding_spans else 1.0,
        "hypotheses": _hypotheses(formatted_clusters, lnc_candidates),
    }


def _hypotheses(clusters: list[dict], lnc: list[dict]) -> list[str]:
    out = []
    for c in clusters:
        out.append(f"Putative enhancer at {c['start']}-{c['end']} with {c['n_motifs']} TF motifs "
                   f"({', '.join(c['tfs'])}): test by reporter assay + CRISPRi of the element.")
    for l in lnc[:3]:
        out.append(f"lncRNA candidate at {l['start']}-{l['end']} ({l['strand']}): "
                   "validate by RT-PCR and subcellular fractionation.")
    return out

# Multi-scale probabilistic inference using explicit biophysical/statistical
# surrogates. There is no trained foundation model and not clinically validated.
import math
import numpy as np
from collections import Counter

def coordinate_field(seq,cell_state=None,bin_size=50):
    """Continuous per-bin regulatory embedding from sequence and cell state."""
    s=clean_dna(seq); state={"atac":.5,"h3k27ac":.5,"methylation":.5,**(cell_state or {})}; bins=[]
    for i in range(0,len(s),bin_size):
        w=s[i:i+bin_size]; gc=gc_content(w); motif_density=sum(len(find_motif(w,m)) for m in TF_MOTIFS.values())/max(1,len(w)); potential=.3*gc+.3*state['atac']+.25*state['h3k27ac']+.1*(1-state['methylation'])+.05*min(1,motif_density*20); bins.append({"start":i,"end":i+len(w),"gc":gc,"motif_density":motif_density,"regulatory_potential":potential})
    return {"bin_size":bin_size,"cell_state":state,"field":bins}

def chromatin_graph(seq,contacts=None,bin_size=100):
    field=coordinate_field(seq,bin_size=bin_size)['field']; n=len(field); edges=[]
    if contacts is None:
        for i in range(n):
            for j in range(i+1,n):
                weight=(1+abs(i-j))**-.8
                if weight>.15: edges.append({"source":i,"target":j,"contact":weight})
    else:
        matrix=np.asarray(contacts,float)
        if matrix.shape!=(n,n): raise ValueError(f"contacts must have shape {(n,n)}")
        for i in range(n):
            for j in range(i+1,n):
                if matrix[i,j]>0: edges.append({"source":i,"target":j,"contact":float(matrix[i,j])})
    return {"nodes":field,"edges":edges,"bin_size":bin_size}

def graph_propagate(graph,perturbations=None,steps=3,damping=.6):
    if steps<0 or not 0<=damping<=1: raise ValueError("invalid propagation values")
    n=len(graph['nodes']); state=np.array([x['regulatory_potential'] for x in graph['nodes']],float)
    for i,value in (perturbations or {}).items(): state[int(i)]+=float(value)
    adjacency=np.zeros((n,n))
    for e in graph['edges']: adjacency[e['source'],e['target']]=adjacency[e['target'],e['source']]=e['contact']
    rows=adjacency.sum(axis=1,keepdims=True); normalized=np.divide(adjacency,rows,out=np.zeros_like(adjacency),where=rows>0); initial=state.copy()
    for _ in range(steps): state=(1-damping)*initial+damping*normalized@state
    return {"initial":initial.tolist(),"propagated":state.tolist(),"delta":(state-initial).tolist(),"steps":steps}

def motif_binding_energy(sequence,motif):
    s=clean_dna(sequence); motif=motif.upper(); scores=[]
    for i in range(max(0,len(s)-len(motif)+1)):
        match=sum(a==b or b in 'NRWYKMSVHD' for a,b in zip(s[i:i+len(motif)],motif))/len(motif); shape=.5*(s[i:i+len(motif)].count('A')+s[i:i+len(motif)].count('T'))/len(motif); scores.append({"position":i,"match":match,"minor_groove_proxy":shape,"energy_kcal_mol":-8*match+.8*shape})
    return min(scores,key=lambda x:x['energy_kcal_mol']) if scores else {"position":None,"match":0,"minor_groove_proxy":0,"energy_kcal_mol":0}

def nucleosome_positioning(seq,window=147,step=25):
    s=clean_dna(seq); out=[]
    for i in range(0,max(1,len(s)-window+1),step):
        w=s[i:i+window]; periodic=sum(w[j] in 'AT' and w[j+10] in 'AT' for j in range(max(0,len(w)-10)))/max(1,len(w)-10); score=min(1,.25+.45*gc_content(w)+.3*periodic); out.append({"start":i,"end":i+len(w),"occupancy":score})
    return out

def enhancer_gene_causality(enhancer_activity,gene_expression,perturbation=None):
    x=np.asarray(enhancer_activity,float); y=np.asarray(gene_expression,float)
    if x.shape!=y.shape or x.size<3: raise ValueError("matched signals with at least 3 samples required")
    observational=0 if x.std()==0 or y.std()==0 else float(np.corrcoef(x,y)[0,1]); causal=None
    if perturbation is not None:
        z=np.asarray(perturbation,bool)
        if z.shape!=x.shape or z.all() or (~z).all(): raise ValueError("perturbation must contain treated and control samples")
        causal=float(y[z].mean()-y[~z].mean())
    return {"observational_correlation":observational,"interventional_effect":causal,"evidence":"interventional" if causal is not None else "associational only"}

def regulatory_logic(motif_activities,logic="AND"):
    values=[float(v) for v in motif_activities]; op=logic.upper()
    if any(not 0<=v<=1 for v in values) or not values: raise ValueError("activities must be non-empty fractions")
    if op=='AND': result=float(np.prod(values))
    elif op=='OR': result=1-float(np.prod([1-v for v in values]))
    elif op=='NOT' and len(values)==1: result=1-values[0]
    else: raise ValueError("logic must be AND/OR or unary NOT")
    return {"logic":op,"activity":result}

def cell_state_decode(seq,cell_states):
    return {name:coordinate_field(seq,state)['field'] for name,state in cell_states.items()}

def temporal_trajectory(initial_state,transition_matrix,steps=10):
    state=np.asarray(initial_state,float); matrix=np.asarray(transition_matrix,float)
    if matrix.shape!=(len(state),len(state)) or np.any(matrix<0) or not np.allclose(matrix.sum(axis=1),1): raise ValueError("transition matrix must be nonnegative row-stochastic")
    history=[state.tolist()]
    for _ in range(steps): state=state@matrix; history.append(state.tolist())
    return {"trajectory":history,"final_state":history[-1]}

def variant_counterfactual(seq,pos,alt,cell_states=None,samples=500,seed=0):
    s=clean_dna(seq)
    if not 0<=pos<len(s): raise ValueError("pos outside sequence")
    alt=clean_dna(alt)
    if len(alt)!=1: raise ValueError("alt must be one base")
    mutant=s[:pos]+alt+s[pos+1:]; states=cell_states or {"generic":{"atac":.5,"h3k27ac":.5,"methylation":.5}}; rng=np.random.default_rng(seed); outcomes={}
    for name,state in states.items():
        ref=np.mean([x['regulatory_potential'] for x in coordinate_field(s,state)['field']]); mut=np.mean([x['regulatory_potential'] for x in coordinate_field(mutant,state)['field']]); tf_delta=sum(motif_binding_energy(mutant,m)['energy_kcal_mol']-motif_binding_energy(s,m)['energy_kcal_mol'] for m in TF_MOTIFS.values())/len(TF_MOTIFS); nuc_delta=np.mean([x['occupancy'] for x in nucleosome_positioning(mutant)])-np.mean([x['occupancy'] for x in nucleosome_positioning(s)]); mean=(mut-ref)+.02*tf_delta-.1*nuc_delta; draws=rng.normal(mean,.03+1/math.sqrt(len(s)),samples)
        outcomes[name]={"delta_regulatory_potential":mut-ref,"delta_tf_energy":tf_delta,"delta_nucleosome":nuc_delta,"expression_delta_mean":float(draws.mean()),"expression_delta_std":float(draws.std()),"ci90":[float(np.quantile(draws,.05)),float(np.quantile(draws,.95))]}
    return {"ref":s[pos],"alt":alt,"position":pos,"cell_states":outcomes,"seed":seed,"samples":samples}

def perturbation_blueprint(seq,target_expression_delta,cell_state=None,top_n=5):
    s=clean_dna(seq); state=cell_state or {}; baseline=np.mean([x['regulatory_potential'] for x in coordinate_field(s,state)['field']]); options=[]
    for pos in range(len(s)):
        for alt in 'ACGT':
            if alt==s[pos]: continue
            mutant=s[:pos]+alt+s[pos+1:]; changed=np.mean([x['regulatory_potential'] for x in coordinate_field(mutant,state)['field']]); delta=changed-baseline; risk=min(1,sum(len(find_motif(mutant,m)) for m in TF_MOTIFS.values())/max(1,len(s)/20)); reward=-abs(delta-target_expression_delta)-.1*risk; options.append({"type":"base_edit","position":pos,"ref":s[pos],"alt":alt,"predicted_delta":delta,"off_target_regulatory_risk":risk,"reward":reward})
    options.sort(key=lambda x:(-x['reward'],x['position'],x['alt'])); return {"target_delta":target_expression_delta,"strategies":options[:top_n],"method":"exhaustive transparent counterfactual search"}

def perturbation_feedback(prior,observed_effect,observed_std=.1):
    mean=float(prior['mean']); std=float(prior['std'])
    if min(std,observed_std)<=0: raise ValueError("uncertainties must be positive")
    p=1/std**2; q=1/observed_std**2; post=(p*mean+q*observed_effect)/(p+q); return {"mean":post,"std":math.sqrt(1/(p+q)),"prior_mean":mean,"observed":observed_effect}

def regulatory_blueprint(seq,cell_state=None):
    decoded=decode(seq); graph=chromatin_graph(seq); field=coordinate_field(seq,cell_state); return {"elements":decoded,"coordinate_field":field,"causal_graph":graph,"propagated_state":graph_propagate(graph),"prioritized_interventions":perturbation_blueprint(seq[:min(len(clean_dna(seq)),60)],.05,cell_state,3),"model_status":"Transparent biophysical/statistical surrogates; no trained foundation model and not clinically validated.","validation":["Test enhancer causality with matched perturbation and expression readouts.","Compare predicted contacts against cell-state Hi-C or Micro-C.","Feed count-level perturbation effects back into uncertainty updates."]}

def dark_genome_diagnostics(seq,cell_state=None):
    s=clean_dna(seq); d=decode(s); field=coordinate_field(s,cell_state)['field']; graph=chromatin_graph(s,bin_size=max(25,min(100,len(s)))); occ=nucleosome_positioning(s); potentials=np.array([x['regulatory_potential'] for x in field]); densities=np.array([x['motif_density'] for x in field]); occupancy=np.array([x['occupancy'] for x in occ]); out={"length":float(len(s)),"gc_fraction":gc_content(s),"at_fraction":1-gc_content(s),"dark_matter_fraction":float(d['dark_matter_fraction']),"tf_motif_count":float(len(d['tf_motif_hits'])),"enhancer_cluster_count":float(len(d['enhancer_clusters'])),"cpg_island_count":float(len(d['cpg_islands'])),"lncrna_candidate_count":float(len(d['lncrna_candidates'])),"regulatory_potential_mean":float(potentials.mean()),"regulatory_potential_std":float(potentials.std()),"regulatory_potential_min":float(potentials.min()),"regulatory_potential_max":float(potentials.max()),"motif_density_mean":float(densities.mean()),"motif_density_max":float(densities.max()),"graph_node_count":float(len(graph['nodes'])),"graph_edge_count":float(len(graph['edges'])),"graph_mean_degree":2*len(graph['edges'])/max(1,len(graph['nodes'])),"nucleosome_mean":float(occupancy.mean()),"nucleosome_std":float(occupancy.std()),"nucleosome_min":float(occupancy.min()),"nucleosome_max":float(occupancy.max()),"sequence_entropy":float(-sum((s.count(b)/len(s))*math.log2(s.count(b)/len(s)) for b in 'ACGT' if s.count(b)))}
    for b in 'ACGT': out[f'base_fraction.{b}']=s.count(b)/len(s)
    for tf,motif in TF_MOTIFS.items(): out[f'binding_energy.{tf}']=float(motif_binding_energy(s,motif)['energy_kcal_mol'])
    return out
