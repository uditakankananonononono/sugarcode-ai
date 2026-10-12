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
    """Regulatory-motif and composition calculations over a supplied sequence; no throughput guarantee."""
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
    """Context-relative substitution and motif-difference calculation.

    Calls the local variant helper with a context-relative c. coordinate; no
    transcript mapping or codon consequence is supplied by this function.
    TF motifs are compared; CTCF anchors are not scanned here.
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

def _track_values(tracks, state, bins):
    """Scalar or exact-length per-bin inputs; no inferred ATAC/ChIP signal."""
    if tracks is None:
        tracks = {}
    if not isinstance(tracks, dict) or set(tracks) - set(state):
        raise ValueError("tracks must contain only atac, h3k27ac, methylation")
    result = {}
    for name, default in state.items():
        value = tracks.get(name, default)
        if isinstance(value, (list, tuple, np.ndarray)):
            if len(value) != bins:
                raise ValueError("track length must equal sequence bin count")
            values = list(value)
        else:
            values = [value] * bins
        if any(isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, float, np.integer, np.floating))
               or not math.isfinite(float(v)) or not 0 <= float(v) <= 1 for v in values):
            raise ValueError("track values must be finite scalars in [0,1]")
        result[name] = list(map(float, values))
    return result


def epigenetic_fusion(seq,tracks=None,cell_type="generic",bin_size=100):
    """Combine sequence GC with supplied scalar/per-bin tracks or fixed priors."""
    if type(bin_size) is not int or bin_size <= 0:
        raise ValueError("bin_size must be a positive integer")
    s=clean_dna(seq); state=CELL_STATES.get(cell_type,CELL_STATES['generic'])
    track_values=_track_values(tracks,state,math.ceil(len(s)/bin_size))
    bins=[]
    for number,i in enumerate(range(0,len(s),bin_size)):
        w=s[i:i+bin_size]; atac=track_values['atac'][number]; hist=track_values['h3k27ac'][number]; meth=track_values['methylation'][number]
        gc=gc_content(w); activity=.35*gc+.3*atac+.25*hist+.1*(1-meth)
        bins.append({"start":i,"end":i+len(w),"gc":gc,"atac":atac,"h3k27ac":hist,"methylation":meth,"regulatory_activity":activity})
    return {"cell_type":cell_type,"bins":bins,"mean_activity":float(np.mean([b['regulatory_activity'] for b in bins]))}

def contact_probability(distance_bp,ctcf_convergent=False,cohesin_residence_min=20,insulation=.2):
    if distance_bp<1 or cohesin_residence_min<=0 or not 0<=insulation<=1: raise ValueError("invalid contact parameters")
    base=(distance_bp/1000)**-.75; extrusion=1-math.exp(-cohesin_residence_min/20); orientation=1.8 if ctcf_convergent else .7
    return min(1.0,base*extrusion*orientation*(1-insulation))

def reconstruct_contact_map(seq,bin_size=1000):
    """Distance-decay proxy map with a fixed orientation multiplier between convergent CTCF sites
    (forward-strand motif upstream of a reverse-strand motif), both strands scanned."""
    s=clean_dna(seq); n=math.ceil(len(s)/bin_size); matrix=np.zeros((n,n))
    fwd=set(p//bin_size for p in find_motif(s,CTCF_MOTIF))
    rev=set((len(s)-p-len(CTCF_MOTIF))//bin_size for p in find_motif(reverse_complement(s),CTCF_MOTIF))
    for i in range(n):
        for j in range(i,n): matrix[i,j]=matrix[j,i]=1.0 if i==j else contact_probability((j-i)*bin_size,i in fwd and j in rev)
    return {"bin_size":bin_size,"matrix":matrix.tolist(),"bins":n,"ctcf_forward_bins":sorted(fwd),"ctcf_reverse_bins":sorted(rev)}

def tad_boundaries(seq,bin_size=1000,min_drop=.05):
    """Insulation-score boundaries: full-window bins whose insulation is a local minimum at least
    ``min_drop`` (fractional) below the highest bin within two bins. Plain distance decay with no
    CTCF motifs gives equal full-window scores in this fixed distance-decay
    matrix, so this helper emits no boundaries. This is not a genomic guarantee."""
    cmap=np.asarray(reconstruct_contact_map(seq,bin_size)['matrix']); n=len(cmap)
    insulation={i:float(cmap[i-2:i,i+1:i+3].mean()) for i in range(2,n-2)}
    out=[]
    for i,v in insulation.items():
        near=[insulation[j] for j in range(i-2,i+3) if j!=i and j in insulation]
        if near and v<=min(near) and v<(1-min_drop)*max(near):
            out.append({"position":i*bin_size,"insulation_score":v})
    return out

_IUPAC={"A":"A","C":"C","G":"G","T":"T","R":"AG","Y":"CT","S":"GC","W":"AT","K":"GT","M":"AC","B":"CGT","D":"AGT","H":"ACT","V":"ACG","N":"ACGT"}

def _match_fraction(window,motif):
    return sum(b in _IUPAC.get(m,m) for b,m in zip(window,motif))/len(motif)

def motif_energy(seq,motif):
    """Best IUPAC-aware match of ``motif`` in ``seq`` (a degenerate code only matches its own bases)."""
    s=clean_dna(seq); motif=motif.upper(); best=0.0
    for i in range(max(0,len(s)-len(motif)+1)):
        best=max(best,_match_fraction(s[i:i+len(motif)],motif))
    return {"best_match_fraction":best,"binding_energy_kcal_mol":-7.5*best}

CTCF_MOTIF="CCGCGNGGNGGCAG"

def local_tf_binding(seq,pos,motifs=None):
    """Per-factor best match over the windows that contain ``pos`` (both strands)."""
    s=clean_dna(seq); motifs=motifs or {**TF_MOTIFS,"CTCF":CTCF_MOTIF}; out={}
    for tf,motif in motifs.items():
        m=motif.upper()
        best=0.0
        for i in range(max(0,pos-len(m)+1),min(pos,len(s)-len(m))+1):
            w=s[i:i+len(m)]
            best=max(best,_match_fraction(w,m),_match_fraction(reverse_complement(w),m))
        out[tf]={"best_match_fraction":best,"binding_energy_kcal_mol":-7.5*best}
    return out

def nucleosome_occupancy(seq):
    s=clean_dna(seq); gc=gc_content(s); periodic=sum(s[i] in 'AT' and s[i+10] in 'AT' for i in range(max(0,len(s)-10)))/max(1,len(s)-10)
    return min(1,max(0,.25+.5*gc+.25*periodic))

def expression_prediction(seq,cell_type="generic",contacts=None,tracks=None,bin_size=100):
    fusion=epigenetic_fusion(seq,tracks=tracks,cell_type=cell_type,bin_size=bin_size); promoter=motif_energy(seq,"TATAWAW")['best_match_fraction']; contacts=contacts if contacts is not None else fusion['mean_activity']; log_expression=-1+2*fusion['mean_activity']+promoter+math.log1p(contacts)
    return {"cell_type":cell_type,"log2_expression":log_expression,"relative_expression":2**log_expression,"components":{"regulatory_activity":fusion['mean_activity'],"promoter":promoter,"contact":contacts}}

def delta_embedding(ref,alt):
    """Vector deltas with explicit zero-vector cosine convention."""
    a=sequence_embedding(ref); b=sequence_embedding(alt); delta=b-a
    norms=float(np.linalg.norm(a)*np.linalg.norm(b))
    if np.array_equal(a,b):
        cosine_change=0.0
    elif norms == 0:
        cosine_change=1.0
    else:
        cosine_change=float(np.clip(1-np.dot(a,b)/norms,0,2))
    return {"l2":float(np.linalg.norm(delta)),"l1":float(np.abs(delta).sum()),"cosine_change":cosine_change,"delta":delta.tolist()}

def variant_mechanistic_deltas(seq,pos,alt,cell_type="generic"):
    s=clean_dna(seq)
    if not 0<=pos<len(s): raise ValueError("pos outside context")
    alt=clean_dna(alt)
    if len(alt)!=1: raise ValueError("alt must be one base")
    mutant=s[:pos]+alt+s[pos+1:]; ref_expr=expression_prediction(s,cell_type); alt_expr=expression_prediction(mutant,cell_type); emb=delta_embedding(s,mutant); ref_atac=epigenetic_fusion(s,cell_type=cell_type)['mean_activity']; alt_atac=epigenetic_fusion(mutant,cell_type=cell_type)['mean_activity']; ref_ctcf=motif_energy(s,"CCGCGNGGNGGCAG"); alt_ctcf=motif_energy(mutant,"CCGCGNGGNGGCAG")
    ref_local=local_tf_binding(s,pos); alt_local=local_tf_binding(mutant,pos)
    tf_deltas={tf:alt_local[tf]['binding_energy_kcal_mol']-ref_local[tf]['binding_energy_kcal_mol'] for tf in ref_local if max(ref_local[tf]['best_match_fraction'],alt_local[tf]['best_match_fraction'])==1.0 and alt_local[tf]['best_match_fraction']!=ref_local[tf]['best_match_fraction']}  # a full site destroyed or created at pos
    uncertainty=.05+1/math.sqrt(max(1,len(s)))
    return {"ref":s[pos],"alt":alt,"delta_embedding_l2":emb['l2'],"delta_tf_binding_kcal_mol":sum(tf_deltas.values()),"delta_tf_binding_by_factor":tf_deltas,"delta_ctcf_binding_kcal_mol":alt_ctcf['binding_energy_kcal_mol']-ref_ctcf['binding_energy_kcal_mol'],"delta_atac":alt_atac-ref_atac,"delta_nucleosome":nucleosome_occupancy(mutant)-nucleosome_occupancy(s),"delta_contact":(alt_ctcf['best_match_fraction']-ref_ctcf['best_match_fraction'])*.1,"delta_rna_expression":alt_expr['log2_expression']-ref_expr['log2_expression'],"uncertainty_std":uncertainty}

def simulate_edit(seq,start,end,replacement,cell_type="generic",contact_bin_size=1000):
    """Re-score a substitution, insertion (start==end) or deletion (empty replacement)."""
    s=clean_dna(seq)
    if not 0<=start<=end<=len(s): raise ValueError("invalid edit interval")
    if replacement and any(c not in "ACGTNacgtn" for c in replacement): raise ValueError("replacement must be DNA")
    insert=clean_dna(replacement) if replacement else ""
    edited=s[:start]+insert+s[end:]
    if not edited: raise ValueError("edit deletes the whole sequence")
    ref=expression_prediction(s,cell_type); alt=expression_prediction(edited,cell_type)
    kind="deletion" if not insert else "insertion" if start==end else "substitution"
    return {"edit_type":kind,"edited_sequence":edited,"length_delta":len(edited)-len(s),"motifs_ref":analyze_sequence(s)['tf_motifs'],"motifs_edited":analyze_sequence(edited)['tf_motifs'],"expression_delta":alt['log2_expression']-ref['log2_expression'],"ctcf_boundary_delta":motif_energy(edited,CTCF_MOTIF)['best_match_fraction']-motif_energy(s,CTCF_MOTIF)['best_match_fraction'],"enhancer_hijack_risk":max(0,alt['relative_expression']-ref['relative_expression'])/(1+ref['relative_expression']),"chromatin_comparison":compare_edit_chromatin(s,edited,contact_bin_size)}

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

# Splice-site position frequency matrices (A,C,G,T), consensus after Shapiro & Senapathy 1987:
# donor MAG|GURAGU (3 exonic + 6 intronic), acceptor (Y)10 N C A G | G.
_DONOR=[(.35,.35,.18,.12),(.60,.13,.14,.13),(.08,.04,.81,.07),(0,0,1,0),(0,0,0,1),(.49,.03,.45,.03),(.71,.07,.12,.10),(.06,.05,.84,.05),(.15,.19,.19,.47)]
_ACCEPTOR=[(.08,.40,.07,.45)]*10+[(.25,.25,.25,.25),(.04,.65,.03,.28),(1,0,0,0),(0,0,1,0),(.24,.14,.52,.10)]

def _pwm_scores(s,pwm):
    idx={"A":0,"C":1,"G":2,"T":3}; best=sum(math.log2(max(col)/.25) for col in pwm); scores=[]
    for i in range(len(s)-len(pwm)+1):
        total=0.0
        for b,col in zip(s[i:i+len(pwm)],pwm):
            p=col[idx[b]] if b in idx else .25
            if p<=0: total=None; break
            total+=math.log2(p/.25)
        if total is not None: scores.append((i,total/best))
    return scores

def splice_sites(seq,threshold=.8):
    """Donor/acceptor sites scoring at least ``threshold`` of the consensus log-odds maximum."""
    s=clean_dna(seq)
    donors=[{"position":i+3,"score":round(v,3)} for i,v in _pwm_scores(s,_DONOR) if v>=threshold]
    acceptors=[{"position":i+14,"score":round(v,3)} for i,v in _pwm_scores(s,_ACCEPTOR) if v>=threshold]
    return {"donors":donors,"acceptors":acceptors}

def cryptic_splice_risk(seq):
    """Risk from the strongest donor/acceptor match: ~0 for no consensus-like site, ->1 near consensus."""
    s=clean_dna(seq); best=max([v for _,v in _pwm_scores(s,_DONOR)]+[v for _,v in _pwm_scores(s,_ACCEPTOR)]+[0.0])
    return 1/(1+math.exp(-(best-.8)*20))

def propose_regulatory_edits(seq,target_delta,cell_type="generic",max_edits=1):
    s=clean_dna(seq); baseline=expression_prediction(s,cell_type)['log2_expression']; candidates=[]
    for pos in range(len(s)):
        for base in 'ACGT':
            if base==s[pos]: continue
            mutant=s[:pos]+base+s[pos+1:]; delta=expression_prediction(mutant,cell_type)['log2_expression']-baseline; safety=1-cryptic_splice_risk(mutant); reward=-abs(delta-target_delta)+.2*safety
            candidates.append({"position":pos,"ref":s[pos],"alt":base,"predicted_expression_delta":delta,"cryptic_splice_risk":1-safety,"reward":reward})
    candidates.sort(key=lambda x:(-x['reward'],x['position'],x['alt'])); return {"target_delta":target_delta,"cell_type":cell_type,"edits":candidates[:max_edits],"method":"exhaustive minimal-edit search over transparent surrogates"}

def cell_state_contrast(seq,cell_types=("hepatocyte","neuron"),tracks_by_cell=None,bin_size=100):
    """Compare supplied sequence under cell priors and optional per-cell tracks."""
    if not cell_types or len(set(cell_types)) != len(cell_types):
        raise ValueError("distinct nonempty cell types required")
    tracks_by_cell=tracks_by_cell or {}
    if set(tracks_by_cell)-set(cell_types):
        raise ValueError("track cell must appear in cell_types")
    results={c:expression_prediction(seq,c,tracks=tracks_by_cell.get(c),bin_size=bin_size) for c in cell_types}
    vals=[r['log2_expression'] for r in results.values()]
    return {"states":results,"range_log2":max(vals)-min(vals),"highest":max(results,key=lambda c:results[c]['log2_expression'])}

def genomegpt_diagnostics(seq,cell_type="generic"):
    s=clean_dna(seq); analysis=analyze_sequence(s); fusion=epigenetic_fusion(s,cell_type=cell_type); emb=sequence_embedding(s); contacts=np.asarray(reconstruct_contact_map(s,max(50,min(1000,len(s))))['matrix']); expr=expression_prediction(s,cell_type); masked=masked_sequence_objective(s,seed=0)
    d={"length":float(len(s)),"gc_fraction":gc_content(s),"at_fraction":1-gc_content(s),"motif_count":float(len(analysis['tf_motifs'])),"ctcf_count":float(len(analysis['ctcf_sites'])),"kmer_anomaly_count":float(len(analysis['kmer_anomalies'])),"loop_count":float(len(analysis['long_range'])),"mean_regulatory_activity":fusion['mean_activity'],"nucleosome_occupancy":nucleosome_occupancy(s),"expression_log2":expr['log2_expression'],"relative_expression":expr['relative_expression'],"embedding_l1":float(np.abs(emb).sum()),"embedding_l2":float(np.linalg.norm(emb)),"embedding_entropy":float(-np.sum(emb*np.log2(np.maximum(emb,1e-15)))),"contact_mean":float(contacts.mean()),"contact_std":float(contacts.std()),"contact_max_offdiag":float((contacts-np.eye(len(contacts))).max()) if len(contacts)>1 else 0.,"tad_boundary_count":float(len(tad_boundaries(s,max(50,min(1000,len(s)))))),"masked_perplexity":masked['perplexity'],"masked_cross_entropy":masked['cross_entropy_nats'],"cryptic_splice_risk":cryptic_splice_risk(s)}
    for b in 'ACGT': d[f'base_fraction.{b}']=s.count(b)/len(s)
    for tf,motif in TF_MOTIFS.items(): d[f'motif_energy.{tf}']=motif_energy(s,motif)['binding_energy_kcal_mol']
    return d

def genomegpt_report(seq,cell_type="generic"):
    return {"analysis":analyze_sequence(seq),"epigenetic_fusion":epigenetic_fusion(seq,cell_type=cell_type),"contact_map":reconstruct_contact_map(seq),"tad_boundaries":tad_boundaries(seq),"expression":expression_prediction(seq,cell_type),"cell_state_contrast":cell_state_contrast(seq),"diagnostics":genomegpt_diagnostics(seq,cell_type),"model_status":"Transparent sequence/statistical surrogates; no trained foundation model and not clinically validated.","next_steps":["Compare predictions against matched cell-state ATAC/ChIP/Hi-C data.","Use perturbational measurements to calibrate expression deltas.","Review edit simulations for splice and enhancer-hijack risk before experimental planning."]}



def compare_edit_chromatin(reference,edited,bin_size=1000):
    """Compare motif-loop and contact/insulation proxies; indels lack bin alignment."""
    if type(bin_size) is not int or bin_size <= 0:
        raise ValueError("bin_size must be a positive integer")
    ref=clean_dna(reference); alt=clean_dna(edited)
    if max(math.ceil(len(ref)/bin_size),math.ceil(len(alt)/bin_size)) > 512:
        raise ValueError("contact comparison limited to 512 bins")
    ref_loops=predict_loops(ref);alt_loops=predict_loops(alt)
    ref_map=reconstruct_contact_map(ref,bin_size);alt_map=reconstruct_contact_map(alt,bin_size)
    ref_bounds=tad_boundaries(ref,bin_size);alt_bounds=tad_boundaries(alt,bin_size)
    same_length=len(ref)==len(alt)
    ref_pairs={(r['anchor1'],r['anchor2']) for r in ref_loops}
    alt_pairs={(r['anchor1'],r['anchor2']) for r in alt_loops}
    def insulation(matrix):
        m=np.asarray(matrix,float)
        return [{'position':i*bin_size,'proxy':float(m[i-2:i,i+1:i+3].mean())} for i in range(2,len(m)-2)]
    ref_ins=insulation(ref_map['matrix']);alt_ins=insulation(alt_map['matrix'])
    return {'reference_loops':ref_loops,'edited_loops':alt_loops,
            'lost_loops':sorted(ref_pairs-alt_pairs) if same_length else None,
            'created_loops':sorted(alt_pairs-ref_pairs) if same_length else None,
            'reference_contact_map':ref_map,'edited_contact_map':alt_map,
            'contact_delta':(np.asarray(alt_map['matrix'])-np.asarray(ref_map['matrix'])).tolist() if same_length else None,
            'reference_boundaries':ref_bounds,'edited_boundaries':alt_bounds,
            'reference_insulation':ref_ins,'edited_insulation':alt_ins,
            'insulation_delta':[{'position':r['position'],'proxy_delta':a['proxy']-r['proxy']} for r,a in zip(ref_ins,alt_ins)] if same_length else None,
            'comparison_status':'same_length_common_bins' if same_length else 'length_change_not_coordinate_aligned',
            'biological_effect_established':False,
            'scope':'Motif/distance-decay proxy comparison only; no learned 3D model or experimental contact signal.'}


def propose_expression_profile_edits(seq,targets,*,tolerances=None,preserve_cells=None,
                                     tracks_by_cell=None,max_candidates=10):
    """Rank single substitutions meeting supplied per-cell scalar constraints.

    Targets are log2-expression proxy deltas, not per-gene expression profiles.
    The search has no reinforcement learning or off-target genomic assessment.
    """
    s=clean_dna(seq)
    if len(s)>1000:raise ValueError("profile search limited to 1000 sequence bases")
    if type(max_candidates) is not int or not 1<=max_candidates<=100:raise ValueError("max_candidates must be 1..100")
    if not isinstance(targets,dict) or not 1<=len(targets)<=8:raise ValueError("1..8 target cells required")
    tolerances={} if tolerances is None else dict(tolerances)
    preserve_cells={} if preserve_cells is None else dict(preserve_cells)
    tracks_by_cell={} if tracks_by_cell is None else dict(tracks_by_cell)
    if set(tolerances)-set(targets) or set(targets)&set(preserve_cells):raise ValueError("target/tolerance/preserved cell mismatch")
    cells=list(targets)+list(preserve_cells)
    if len(cells)>8 or set(tracks_by_cell)-set(cells):raise ValueError("at most 8 matching cell constraints")
    for cell in cells:
        if not isinstance(cell,str) or not cell.strip():raise ValueError("cell name required")
    for values in (targets,tolerances,preserve_cells):
        for value in values.values():
            if type(value) not in (int,float) or not math.isfinite(value):raise ValueError("finite scalar constraints required")
    if any(v<0 for v in tolerances.values()) or any(v<0 for v in preserve_cells.values()):raise ValueError("tolerances nonnegative")
    baseline={c:expression_prediction(s,c,tracks=tracks_by_cell.get(c))['log2_expression'] for c in cells}
    candidates=[]
    for pos in range(len(s)):
        for base in 'ACGT':
            if base==s[pos]:continue
            mutant=s[:pos]+base+s[pos+1:]
            deltas={c:expression_prediction(mutant,c,tracks=tracks_by_cell.get(c))['log2_expression']-baseline[c] for c in cells}
            errors={c:abs(deltas[c]-targets[c]) for c in targets}
            if any(errors[c]>tolerances.get(c,.05) for c in targets):continue
            if any(abs(deltas[c])>preserve_cells[c] for c in preserve_cells):continue
            risk=cryptic_splice_risk(mutant)
            candidates.append({'position':pos,'ref':s[pos],'alt':base,'per_cell_delta':deltas,
                               'target_errors':errors,'splice_proxy':risk,'score':-sum(errors.values())+.2*(1-risk),
                               'constraint_satisfied':True})
    candidates.sort(key=lambda r:(-r['score'],r['position'],r['alt']))
    return {'targets':dict(targets),'tolerances':tolerances,'preserve_cells':preserve_cells,
            'edits':candidates[:max_candidates],'searched_substitutions':sum(4-(b in 'ACGT') for b in s),
            'biological_effect_established':False,
            'scope':'Bounded exhaustive single-substitution search over supplied per-cell scalar proxy constraints.'}
