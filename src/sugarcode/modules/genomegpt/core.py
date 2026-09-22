from __future__ import annotations
import math
from collections import Counter
from ...bio.sequence import clean_dna, gc_content, find_motif, reverse_complement
from ..dark_genome.core import TF_MOTIFS
from ..openclinvar.core import interpret_variant


def _kmer_zscores(s: str, k: int = 6) -> list[dict]:
    """Over/under-represented k-mers vs mononucleotide expectation (z-score)."""
    n = len(s) - k + 1
    if n <= 0:
        return []
    counts = Counter(s[i:i + k] for i in range(n))
    p = {b: s.count(b) / len(s) for b in "ACGT"}
    out = []
    for kmer, c in counts.items():
        exp = n
        for b in kmer:
            exp *= p.get(b, 0.001)
        if exp < 1:
            continue
        z = (c - exp) / math.sqrt(exp)
        if abs(z) >= 3:
            out.append({"kmer": kmer, "count": c, "expected": round(exp, 2),
                        "z": round(z, 2)})
    return sorted(out, key=lambda x: -abs(x["z"]))[:20]


def analyze_sequence(seq: str) -> dict:
    """Regulatory-motif and compositional analysis of raw sequence at scale."""
    s = clean_dna(seq)
    motifs = []
    for name, motif in TF_MOTIFS.items():
        for pos in find_motif(s, motif):
            motifs.append({"tf": name, "position": pos})
    # CTCF is the canonical loop-anchor factor; scan its motif explicitly
    ctcf = find_motif(s, "CCGCGNGGNGGCAG")
    return {
        "length": len(s),
        "gc_content": round(gc_content(s), 4),
        "tf_motifs": sorted(motifs, key=lambda m: m["position"]),
        "ctcf_sites": ctcf,
        "kmer_anomalies": _kmer_zscores(s),
        "long_range": predict_loops(s),
    }


def predict_loops(seq: str, min_span: int = 2000) -> list[dict]:
    """Predict 3D chromatin loops from convergent CTCF motif pairs.

    Loop anchors form between a forward-strand CTCF and a downstream
    reverse-strand CTCF (convergent orientation rule).
    """
    s = clean_dna(seq)
    motif = "CCGCGNGGNGGCAG"
    fwd = find_motif(s, motif)
    rev = [len(s) - p - len(motif) for p in find_motif(reverse_complement(s), motif)]
    loops = []
    for a in fwd:
        for b in rev:
            if b - a >= min_span:
                loops.append({"anchor1": a, "anchor2": b, "span": b - a,
                              "orientation": "convergent",
                              "confidence": round(min(1.0, 20000 / (b - a)), 3)})
    return sorted(loops, key=lambda l: -l["confidence"])


def interpret_sequence_variant(gene: str, seq_context: str, pos: int, alt: str,
                               **kwargs) -> dict:
    """Clinical reading of a variant inside its sequence context.

    Combines codon-level consequence with motif-disruption analysis: does the
    change break a TF motif or CTCF anchor?
    """
    s = clean_dna(seq_context)
    if not 0 <= pos < len(s):
        raise ValueError("pos outside context")
    ref = s[pos]
    alt = clean_dna(alt)[0]
    mutant = s[:pos] + alt + s[pos + 1:]
    broken, created = [], []
    for name, motif in TF_MOTIFS.items():
        ref_hits = set(find_motif(s, motif))
        alt_hits = set(find_motif(mutant, motif))
        for h in ref_hits - alt_hits:
            if h <= pos < h + len(motif):
                broken.append({"tf": name, "position": h})
        for h in alt_hits - ref_hits:
            if h <= pos < h + len(motif):
                created.append({"tf": name, "position": h})
    base = interpret_variant(gene, f"c.{pos + 1}{ref}>{alt}", **kwargs)
    reg_impact = "regulatory (non-coding context)" if broken or created else "no motif impact detected"
    return {
        **base,
        "ref_base": ref, "alt_base": alt,
        "motifs_broken": broken, "motifs_created": created,
        "regulatory_impact": reg_impact,
        "noncoding_note": ("Variant alters a regulatory element; can influence gene "
                           "regulation without changing any protein." if broken or created
                           else "No regulatory motif effect found in this context."),
    }

# Advanced multimodal regulatory reasoning. These explicit statistical models
# have no trained foundation-model weights and are not clinically validated.
import numpy as np

CELL_STATES={"generic":{"atac":.5,"h3k27ac":.5,"methylation":.5},"hepatocyte":{"atac":.7,"h3k27ac":.75,"methylation":.35},"neuron":{"atac":.6,"h3k27ac":.55,"methylation":.45}}

def sequence_embedding(seq,k=4):
    """Normalized k-mer state vector, a transparent long-context surrogate."""
    s=clean_dna(seq); keys=["".join(x) for x in __import__('itertools').product('ACGT',repeat=k)]; counts=Counter(s[i:i+k] for i in range(len(s)-k+1)); total=max(1,sum(counts.values()))
    return np.asarray([counts[x]/total for x in keys],float)

def epigenetic_fusion(seq,tracks=None,cell_type="generic",bin_size=100):
    s=clean_dna(seq); state=CELL_STATES.get(cell_type,CELL_STATES['generic']); tracks=tracks or {}
    bins=[]
    for i in range(0,len(s),bin_size):
        w=s[i:i+bin_size]; atac=float(tracks.get('atac',state['atac'])); hist=float(tracks.get('h3k27ac',state['h3k27ac'])); meth=float(tracks.get('methylation',state['methylation'])); gc=gc_content(w); activity=.35*gc+.3*atac+.25*hist+.1*(1-meth); bins.append({"start":i,"end":i+len(w),"gc":gc,"atac":atac,"h3k27ac":hist,"methylation":meth,"regulatory_activity":activity})
    return {"cell_type":cell_type,"bins":bins,"mean_activity":float(np.mean([b['regulatory_activity'] for b in bins]))}

def contact_probability(distance_bp,ctcf_convergent=False,cohesin_residence_min=20,insulation=.2):
    if distance_bp<1 or cohesin_residence_min<=0 or not 0<=insulation<=1: raise ValueError("invalid contact parameters")
    base=(distance_bp/1000)**-.75; extrusion=1-math.exp(-cohesin_residence_min/20); orientation=1.8 if ctcf_convergent else .7
    return min(1.0,base*extrusion*orientation*(1-insulation))

def reconstruct_contact_map(seq,bin_size=1000):
    s=clean_dna(seq); n=math.ceil(len(s)/bin_size); matrix=np.zeros((n,n))
    sites=set(p//bin_size for p in find_motif(s,"CCGCGNGGNGGCAG"))
    for i in range(n):
        for j in range(i,n): matrix[i,j]=matrix[j,i]=1.0 if i==j else contact_probability((j-i)*bin_size,i in sites and j in sites)
    return {"bin_size":bin_size,"matrix":matrix.tolist(),"bins":n}

def tad_boundaries(seq,bin_size=1000):
    cmap=np.asarray(reconstruct_contact_map(seq,bin_size)['matrix']); insulation=[]
    for i in range(1,len(cmap)-1): insulation.append((i,float(cmap[max(0,i-2):i,i+1:min(len(cmap),i+3)].mean())))
    threshold=np.quantile([x[1] for x in insulation],.25) if insulation else 0
    return [{"position":i*bin_size,"insulation_score":v} for i,v in insulation if v<=threshold]

def motif_energy(seq,motif):
    s=clean_dna(seq); motif=motif.upper(); best=0
    for i in range(max(0,len(s)-len(motif)+1)):
        matches=sum(a==b or b in 'NRWYKMSVHD' for a,b in zip(s[i:i+len(motif)],motif)); best=max(best,matches/len(motif))
    return {"best_match_fraction":best,"binding_energy_kcal_mol":-7.5*best}

def nucleosome_occupancy(seq):
    s=clean_dna(seq); gc=gc_content(s); periodic=sum(s[i] in 'AT' and s[i+10] in 'AT' for i in range(max(0,len(s)-10)))/max(1,len(s)-10)
    return min(1,max(0,.25+.5*gc+.25*periodic))

def expression_prediction(seq,cell_type="generic",contacts=None):
    fusion=epigenetic_fusion(seq,cell_type=cell_type); promoter=motif_energy(seq,"TATAWAW")['best_match_fraction']; contacts=contacts if contacts is not None else fusion['mean_activity']; log_expression=-1+2*fusion['mean_activity']+promoter+math.log1p(contacts)
    return {"cell_type":cell_type,"log2_expression":log_expression,"relative_expression":2**log_expression,"components":{"regulatory_activity":fusion['mean_activity'],"promoter":promoter,"contact":contacts}}

def delta_embedding(ref,alt):
    a=sequence_embedding(ref); b=sequence_embedding(alt); delta=b-a
    return {"l2":float(np.linalg.norm(delta)),"l1":float(np.abs(delta).sum()),"cosine_change":float(1-np.dot(a,b)/(max(np.linalg.norm(a)*np.linalg.norm(b),1e-12))),"delta":delta.tolist()}

def variant_mechanistic_deltas(seq,pos,alt,cell_type="generic"):
    s=clean_dna(seq)
    if not 0<=pos<len(s): raise ValueError("pos outside context")
    alt=clean_dna(alt)
    if len(alt)!=1: raise ValueError("alt must be one base")
    mutant=s[:pos]+alt+s[pos+1:]; ref_expr=expression_prediction(s,cell_type); alt_expr=expression_prediction(mutant,cell_type); emb=delta_embedding(s,mutant); ref_atac=epigenetic_fusion(s,cell_type=cell_type)['mean_activity']; alt_atac=epigenetic_fusion(mutant,cell_type=cell_type)['mean_activity']; ref_ctcf=motif_energy(s,"CCGCGNGGNGGCAG"); alt_ctcf=motif_energy(mutant,"CCGCGNGGNGGCAG")
    uncertainty=.05+1/math.sqrt(max(1,len(s)))
    return {"ref":s[pos],"alt":alt,"delta_embedding_l2":emb['l2'],"delta_tf_binding_kcal_mol":alt_ctcf['binding_energy_kcal_mol']-ref_ctcf['binding_energy_kcal_mol'],"delta_atac":alt_atac-ref_atac,"delta_nucleosome":nucleosome_occupancy(mutant)-nucleosome_occupancy(s),"delta_contact":(alt_ctcf['best_match_fraction']-ref_ctcf['best_match_fraction'])*.1,"delta_rna_expression":alt_expr['log2_expression']-ref_expr['log2_expression'],"uncertainty_std":uncertainty}

def simulate_edit(seq,start,end,replacement,cell_type="generic"):
    s=clean_dna(seq)
    if not 0<=start<=end<=len(s): raise ValueError("invalid edit interval")
    edited=s[:start]+clean_dna(replacement)+s[end:]; ref=expression_prediction(s,cell_type); alt=expression_prediction(edited,cell_type)
    return {"edited_sequence":edited,"length_delta":len(edited)-len(s),"motifs_ref":analyze_sequence(s)['tf_motifs'],"motifs_edited":analyze_sequence(edited)['tf_motifs'],"expression_delta":alt['log2_expression']-ref['log2_expression'],"ctcf_boundary_delta":motif_energy(edited,"CCGCGNGGNGGCAG")['best_match_fraction']-motif_energy(s,"CCGCGNGGNGGCAG")['best_match_fraction'],"enhancer_hijack_risk":max(0,alt['relative_expression']-ref['relative_expression'])/(1+ref['relative_expression'])}

def masked_sequence_objective(seq,mask_fraction=.15,seed=0):
    if not 0<mask_fraction<1: raise ValueError("mask_fraction must be in (0,1)")
    s=clean_dna(seq); rng=np.random.default_rng(seed); mask=rng.random(len(s))<mask_fraction; p={b:s.count(b)/len(s) for b in 'ACGT'}; loss=-sum(math.log(max(p[s[i]],1e-12)) for i in range(len(s)) if mask[i])/max(1,mask.sum())
    return {"masked_bases":int(mask.sum()),"cross_entropy_nats":loss,"perplexity":math.exp(loss),"seed":seed}

def modality_alignment(sequence_signal,track_signal):
    a=np.asarray(sequence_signal,float); b=np.asarray(track_signal,float)
    if a.shape!=b.shape or a.size<2: raise ValueError("signals must share shape and have >=2 values")
    if a.std()==0 or b.std()==0: corr=0.0
    else: corr=float(np.corrcoef(a,b)[0,1])
    return {"pearson":corr,"contrastive_loss":1-corr,"mean_absolute_error":float(np.abs(a-b).mean())}

def perturbation_calibration(predicted,observed):
    p=np.asarray(predicted,float); o=np.asarray(observed,float)
    if p.shape!=o.shape or not p.size: raise ValueError("predicted/observed shape mismatch")
    return {"rmse":float(np.sqrt(np.mean((p-o)**2))),"mae":float(np.mean(np.abs(p-o))),"bias":float(np.mean(p-o)),"calibration_slope":float(np.dot(p,o)/max(np.dot(p,p),1e-12))}

def cryptic_splice_risk(seq):
    s=clean_dna(seq); donors=sum(s[i:i+2]=='GT' for i in range(len(s)-1)); acceptors=sum(s[i:i+2]=='AG' for i in range(len(s)-1)); branch=sum(s[i:i+5].startswith('TACT') for i in range(len(s)-4)); return min(1,(donors+acceptors+branch)/max(1,len(s)/20))

def propose_regulatory_edits(seq,target_delta,cell_type="generic",max_edits=1):
    s=clean_dna(seq); baseline=expression_prediction(s,cell_type)['log2_expression']; candidates=[]
    for pos in range(len(s)):
        for base in 'ACGT':
            if base==s[pos]: continue
            mutant=s[:pos]+base+s[pos+1:]; delta=expression_prediction(mutant,cell_type)['log2_expression']-baseline; safety=1-cryptic_splice_risk(mutant); reward=-abs(delta-target_delta)+.2*safety
            candidates.append({"position":pos,"ref":s[pos],"alt":base,"predicted_expression_delta":delta,"cryptic_splice_risk":1-safety,"reward":reward})
    candidates.sort(key=lambda x:(-x['reward'],x['position'],x['alt'])); return {"target_delta":target_delta,"cell_type":cell_type,"edits":candidates[:max_edits],"method":"exhaustive minimal-edit search over transparent surrogates"}

def cell_state_contrast(seq,cell_types=("hepatocyte","neuron")):
    results={c:expression_prediction(seq,c) for c in cell_types}; vals=[r['log2_expression'] for r in results.values()]; return {"states":results,"range_log2":max(vals)-min(vals),"highest":max(results,key=lambda c:results[c]['log2_expression'])}

def genomegpt_diagnostics(seq,cell_type="generic"):
    s=clean_dna(seq); analysis=analyze_sequence(s); fusion=epigenetic_fusion(s,cell_type=cell_type); emb=sequence_embedding(s); contacts=np.asarray(reconstruct_contact_map(s,max(50,min(1000,len(s))))['matrix']); expr=expression_prediction(s,cell_type); masked=masked_sequence_objective(s,seed=0)
    d={"length":float(len(s)),"gc_fraction":gc_content(s),"at_fraction":1-gc_content(s),"motif_count":float(len(analysis['tf_motifs'])),"ctcf_count":float(len(analysis['ctcf_sites'])),"kmer_anomaly_count":float(len(analysis['kmer_anomalies'])),"loop_count":float(len(analysis['long_range'])),"mean_regulatory_activity":fusion['mean_activity'],"nucleosome_occupancy":nucleosome_occupancy(s),"expression_log2":expr['log2_expression'],"relative_expression":expr['relative_expression'],"embedding_l1":float(np.abs(emb).sum()),"embedding_l2":float(np.linalg.norm(emb)),"embedding_entropy":float(-np.sum(emb*np.log2(np.maximum(emb,1e-15)))),"contact_mean":float(contacts.mean()),"contact_std":float(contacts.std()),"contact_max_offdiag":float((contacts-np.eye(len(contacts))).max()) if len(contacts)>1 else 0.,"tad_boundary_count":float(len(tad_boundaries(s,max(50,min(1000,len(s)))))),"masked_perplexity":masked['perplexity'],"masked_cross_entropy":masked['cross_entropy_nats'],"cryptic_splice_risk":cryptic_splice_risk(s)}
    for b in 'ACGT': d[f'base_fraction.{b}']=s.count(b)/len(s)
    for tf,motif in TF_MOTIFS.items(): d[f'motif_energy.{tf}']=motif_energy(s,motif)['binding_energy_kcal_mol']
    return d

def genomegpt_report(seq,cell_type="generic"):
    return {"analysis":analyze_sequence(seq),"epigenetic_fusion":epigenetic_fusion(seq,cell_type=cell_type),"contact_map":reconstruct_contact_map(seq),"tad_boundaries":tad_boundaries(seq),"expression":expression_prediction(seq,cell_type),"cell_state_contrast":cell_state_contrast(seq),"diagnostics":genomegpt_diagnostics(seq,cell_type),"model_status":"Transparent sequence/statistical surrogates; no trained foundation model and not clinically validated.","next_steps":["Compare predictions against matched cell-state ATAC/ChIP/Hi-C data.","Use perturbational measurements to calibrate expression deltas.","Review edit simulations for splice and enhancer-hijack risk before experimental planning."]}
