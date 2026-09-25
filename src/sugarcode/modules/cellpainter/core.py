from __future__ import annotations
import math

# Cell Painting channels: nucleus(DAPI), ER, actin/Golgi(Phalloidin),
# nucleoli/RNA, mitochondria(MitoTracker)
CHANNELS = ["nucleus", "er", "actin_golgi", "nucleoli", "mitochondria"]
FEATURES = ["intensity", "texture", "radial_distribution", "granularity", "compactness"]

MECHANISM_SIGNATURES = {
    "dna_damage": {"nucleus": {"intensity": 1.4, "texture": 1.3, "granularity": 1.5}},
    "microtubule_poison": {"actin_golgi": {"compactness": 0.6, "radial_distribution": 1.4}},
    "mitochondrial_toxin": {"mitochondria": {"intensity": 0.5, "granularity": 0.7}},
    "protein_synthesis_inhibitor": {"nucleoli": {"intensity": 0.6, "compactness": 0.7},
                                    "er": {"intensity": 0.8}},
    "kinase_inhibitor": {"actin_golgi": {"intensity": 0.8, "texture": 1.2},
                         "nucleus": {"compactness": 1.1}},
}


def profile_perturbation(mechanism: str, concentration_uM: float = 1.0,
                         hours: float = 24.0) -> dict:
    """Multiplex staining signature for a perturbation mechanism.

    Signature vectors over channel x feature space, dose/time scaled.
    """
    if mechanism not in MECHANISM_SIGNATURES:
        raise ValueError(f"unknown mechanism {mechanism!r}; reference signatures exist for "
                         f"{sorted(MECHANISM_SIGNATURES)}. For a new compound, profile its images "
                         f"with profile_wells() instead.")
    if concentration_uM < 0 or hours < 0:
        raise ValueError("concentration_uM and hours must be non-negative")
    base = MECHANISM_SIGNATURES[mechanism]
    dose_factor = math.log10(1 + concentration_uM)
    time_factor = min(1.0, hours / 24.0)
    vector = {}
    for ch in CHANNELS:
        for f in FEATURES:
            delta = base.get(ch, {}).get(f, 1.0)
            v = 1.0 + (delta - 1.0) * dose_factor * time_factor
            vector[f"{ch}:{f}"] = round(v, 3)
    distinct = [k for k, v in vector.items() if abs(v - 1.0) > 0.15]
    return {
        "mechanism": mechanism, "dose_uM": concentration_uM, "hours": hours,
        "channels": CHANNELS, "signature_vector": vector,
        "distinctive_features": sorted(distinct),
        "fingerprint_strength": round(sum(abs(v - 1) for v in vector.values()), 3),
    }


def compare_profiles(profiles: list[dict]) -> dict:
    """Pairwise similarity across perturbation profiles; clusters mechanisms."""
    import itertools
    sims = []
    for a, b in itertools.combinations(profiles, 2):
        va, vb = a["signature_vector"], b["signature_vector"]
        keys = set(va) & set(vb)
        # compare DELTAS from the vehicle baseline (1.0): raw vectors are dominated
        # by the constant component, making all pairs spuriously identical (~0.999)
        dot = sum((va[k] - 1.0) * (vb[k] - 1.0) for k in keys)
        na = math.sqrt(sum((va[k] - 1.0) ** 2 for k in keys))
        nb = math.sqrt(sum((vb[k] - 1.0) ** 2 for k in keys))
        sim = dot / (na * nb) if na and nb else 0.0
        sims.append({"pair": [a["mechanism"], b["mechanism"]],
                     "cosine_similarity": round(sim, 4)})
    sims.sort(key=lambda s: -s["cosine_similarity"])
    return {
        "n_profiles": len(profiles),
        "similarities": sims,
        "most_similar_pair": sims[0] if sims else None,
        "novel_mechanism_hint": (sims[-1]["pair"] if sims and sims[-1]["cosine_similarity"] < 0.97
                                 else "all profiles similar"),
    }

import numpy as np

def plate_normalize(features,controls):
 f=np.asarray(features,float); c=np.asarray(controls,float); med=np.median(c,axis=0); mad=np.median(abs(c-med),axis=0); z=(f-med)/(1.4826*mad+1e-9); return {'normalized':z.tolist(),'control_median':med.tolist(),'control_mad':mad.tolist()}
def quality_control(cell_counts,focus_scores,intensities):
 return {'cell_count_cv':float(np.std(cell_counts)/np.mean(cell_counts)),'focus_pass_fraction':float(np.mean(np.asarray(focus_scores)>.7)),'saturation_fraction':float(np.mean(np.asarray(intensities)>=.99)),'pass':np.std(cell_counts)/np.mean(cell_counts)<.3 and np.mean(np.asarray(focus_scores)>.7)>.8}
def batch_correct(batches):
 corrected=[]
 for b in batches:
  x=np.asarray(b,float); corrected.append((x-x.mean(0)).tolist())
 return {'batches':corrected,'method':'within-batch mean centering'}
def nearest_mechanism(query,references):
 q=np.array(list(query['signature_vector'].values()))-1.; rows=[]
 for r in references:
  v=np.array(list(r['signature_vector'].values()))-1.; nq,nv=np.linalg.norm(q),np.linalg.norm(v); sim=float(q@v/(nq*nv)) if nq>0 and nv>0 else 0.; rows.append({'mechanism':r['mechanism'],'similarity':sim})
 return sorted(rows,key=lambda x:-x['similarity'])
def concentration_trajectory(mechanism,doses,hours): return {'profiles':[profile_perturbation(mechanism,d,h) for d in doses for h in hours]}
def cellpainting_report(profiles,controls):
 """Profile-level report. Mechanism matches are leave-one-out: a profile is never matched to itself."""
 matrix=[list(x['signature_vector'].values()) for x in profiles]
 matches=[]
 for i,x in enumerate(profiles):
  others=[r for j,r in enumerate(profiles) if j!=i]
  matches.append({'query':x['mechanism'],'matches':nearest_mechanism(x,others)[:3] if others else []})
 return {'comparison':compare_profiles(profiles),'normalized':plate_normalize(matrix,controls),'mechanism_matches':matches,'model_status':'Profile-only input: hand-specified reference signatures and transparent statistics; no image segmentation on this path. Use profile_wells() to profile real multi-channel images.'}


# ---------------------------------------------------------------------------
# Image path: 5-channel Cell Painting stacks -> per-cell features -> well profiles
# ---------------------------------------------------------------------------
from scipy import ndimage


def validate_stack(image, channels=None) -> np.ndarray:
    """Return a (5, H, W) float stack in CHANNELS order from an array or {channel: 2-D image}."""
    if isinstance(image, dict):
        missing=[c for c in CHANNELS if c not in image]
        if missing: raise ValueError(f"image dict missing channels: {missing}")
        arr=np.stack([np.asarray(image[c],float) for c in CHANNELS])
    else:
        arr=np.asarray(image,float)
        if channels is not None:
            if sorted(channels)!=sorted(CHANNELS): raise ValueError(f"channels must be a permutation of {CHANNELS}")
            arr=arr[[list(channels).index(c) for c in CHANNELS]]
    if arr.ndim!=3 or arr.shape[0]!=len(CHANNELS): raise ValueError(f"image must have shape (5, H, W) for channels {CHANNELS}")
    if min(arr.shape[1:])<16: raise ValueError("each image dimension must be >= 16 px")
    if not np.all(np.isfinite(arr)): raise ValueError("image contains non-finite pixels")
    if np.ptp(arr[0])==0: raise ValueError("nucleus channel has no contrast; cannot segment")
    return arr


def segment_cells(stack, *, cell_radius_px: float=8, min_nucleus_area_px: float=12) -> dict:
    """Segment nuclei on the DNA channel, then grow each nucleus into a cell territory.

    Nuclei: flat-field corrected Otsu threshold with distance-transform splitting
    (bioimage_ai.corrected_segmentation). Cells: each foreground pixel of the
    cytoplasm channels within ``cell_radius_px`` of a nucleus goes to the nearest nucleus.
    """
    from ..bioimage_ai.core import corrected_segmentation
    arr=validate_stack(stack)
    if cell_radius_px<=0: raise ValueError("cell_radius_px must be positive")
    seg=corrected_segmentation(arr[0],min_area_um2=min_nucleus_area_px)
    nuclei=np.asarray(seg["labels"],int)
    if nuclei.max()==0: raise ValueError("no nuclei found in the nucleus channel")
    dist,inds=ndimage.distance_transform_edt(nuclei==0,return_indices=True)
    territory=nuclei[tuple(inds)]*(dist<=cell_radius_px)
    cyto=arr[1:].sum(0); thr=np.percentile(cyto,50)
    cells=np.where((cyto>thr)|(nuclei>0),territory,0)
    return {"nuclei":nuclei,"cells":cells,"n_cells":int(nuclei.max()),"nucleus_threshold":seg["threshold"]}


def _glcm_contrast(values, mask, levels=8):
    v=values.copy(); lo,hi=np.percentile(v[mask],[1,99]) if mask.sum()>1 else (v.min(),v.max())
    q=np.clip(((v-lo)/max(hi-lo,1e-12)*(levels-1)).round(),0,levels-1).astype(int)
    a=q[:,:-1]; b=q[:,1:]; m=mask[:,:-1]&mask[:,1:]
    a2=q[:-1,:]; b2=q[1:,:]; m2=mask[:-1,:]&mask[1:,:]
    pa=np.concatenate([a[m],a2[m2]]); pb=np.concatenate([b[m],b2[m2]])
    if pa.size==0: return 0.0
    return float(np.mean((pa-pb)**2)/(levels-1)**2)


def extract_cell_features(stack, segmentation) -> list[dict]:
    """Per-cell, per-channel features: intensity, texture, radial_distribution, granularity, compactness.

    intensity: mean channel intensity in the cell; texture: GLCM (Haralick) contrast
    on 8 grey levels, horizontal+vertical offsets; radial_distribution: fraction of
    the channel's signal in the outer half of the cell radius from the nucleus centre;
    granularity: fraction of signal removed by a 3x3 grey opening (fine puncta);
    compactness: sqrt(cell area / pi) / intensity-weighted radius of gyration
    (higher = signal concentrated near the nucleus centre).
    """
    arr=validate_stack(stack); cells=np.asarray(segmentation["cells"],int); nuclei=np.asarray(segmentation["nuclei"],int)
    if cells.shape!=arr.shape[1:]: raise ValueError("segmentation must match image shape")
    opened=np.stack([ndimage.grey_opening(arr[c],size=(3,3)) for c in range(len(CHANNELS))])
    ids=[j for j in range(1,int(cells.max())+1) if np.any(cells==j)]
    centers=ndimage.center_of_mass(nuclei>0,nuclei,ids) if ids else []
    rows=[]
    for j,(cy,cx) in zip(ids,centers):
        mask=cells==j; ys,xs=np.nonzero(mask)
        if len(ys)<5: continue
        y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1; sub=mask[y0:y1,x0:x1]
        r=np.hypot(ys-cy,xs-cx); rmax=max(r.max(),1e-9); outer=r>rmax/2
        row={"cell_id":int(j),"area_px":int(mask.sum()),"nucleus_area_px":int(np.sum(nuclei==j))}
        for c,ch in enumerate(CHANNELS):
            v=arr[c][ys,xs]; tot=max(v.sum(),1e-12)
            row[f"{ch}:intensity"]=float(v.mean())
            row[f"{ch}:texture"]=_glcm_contrast(arr[c][y0:y1,x0:x1],sub)
            row[f"{ch}:radial_distribution"]=float(v[outer].sum()/tot)
            row[f"{ch}:granularity"]=float(max(0.0,(v-opened[c][ys,xs]).sum())/tot)
            w=np.clip(v,0,None); rg=math.sqrt(float((w*r**2).sum()/max(w.sum(),1e-12)))
            row[f"{ch}:compactness"]=float(math.sqrt(mask.sum()/math.pi)/max(rg,1e-9))
        rows.append(row)
    if not rows: raise ValueError("no measurable cells")
    return rows


FEATURE_NAMES=[f"{c}:{f}" for c in CHANNELS for f in FEATURES]


def profile_image(stack, **seg_kwargs) -> dict:
    """Segment one field/well and aggregate per-cell features to a median well profile."""
    seg=segment_cells(stack,**seg_kwargs); cells=extract_cell_features(stack,seg)
    mat=np.array([[c[k] for k in FEATURE_NAMES] for c in cells])
    return {"n_cells":len(cells),"profile":dict(zip(FEATURE_NAMES,np.median(mat,0).round(6).tolist())),
            "cell_features":cells,"segmentation":{"nuclei":seg["nuclei"].tolist(),"cells":seg["cells"].tolist()}}


def _reference_direction(mechanism):
    base=MECHANISM_SIGNATURES[mechanism]
    return np.array([math.log(base.get(k.split(':')[0],{}).get(k.split(':')[1],1.0)) for k in FEATURE_NAMES])


def profile_wells(wells, *, control="DMSO", min_cells=5, z_hit=3.0, z_match=2.0, **seg_kwargs) -> dict:
    """Profile a plate of Cell Painting images and compare conditions.

    ``wells``: {well_id: {"condition": name, "image": (5,H,W) stack or channel dict}}.
    Each well is segmented and profiled; features are robust-z-scored against the
    control wells (median/MAD); conditions are summarised by the median z-profile.
    Returns distinctive features (|z| >= z_hit), a condition-by-condition cosine
    similarity matrix, and leave-one-out mechanism annotation: each condition is
    matched to the other (non-control) conditions and scored against each reference
    mechanism by the fraction of that reference's expected feature shifts seen with
    the right sign at |z| >= z_match (contradicting shifts are listed).
    """
    if not wells: raise ValueError("wells must be a non-empty mapping")
    per_well={}; conds={}
    for wid,w in wells.items():
        if "condition" not in w or "image" not in w: raise ValueError(f"well {wid!r} needs 'condition' and 'image'")
        pr=profile_image(w["image"],**seg_kwargs)
        per_well[wid]={"condition":w["condition"],"n_cells":pr["n_cells"],"profile":pr["profile"],"low_cell_count":pr["n_cells"]<min_cells}
        conds.setdefault(w["condition"],[]).append(wid)
    if control not in conds: raise ValueError(f"no control wells with condition {control!r}")
    ctrl=np.array([[per_well[w]["profile"][k] for k in FEATURE_NAMES] for w in conds[control]])
    med=np.median(ctrl,0); mad=np.median(np.abs(ctrl-med),0)
    # floor the scale so features that are flat in controls do not explode
    scale=np.maximum(1.4826*mad,np.maximum(0.05*np.abs(med),1e-6))
    for wid,pw in per_well.items():
        v=np.array([pw["profile"][k] for k in FEATURE_NAMES]); pw["z"]=dict(zip(FEATURE_NAMES,((v-med)/scale).round(4).tolist()))
    summary={}
    for c,ws in conds.items():
        z=np.median([[per_well[w]["z"][k] for k in FEATURE_NAMES] for w in ws],0)
        order=np.argsort(-np.abs(z))
        summary[c]={"wells":ws,"z_profile":dict(zip(FEATURE_NAMES,z.round(4).tolist())),
                    "distinctive_features":[{"feature":FEATURE_NAMES[i],"z":round(float(z[i]),3)} for i in order if abs(z[i])>=z_hit],
                    "phenotype_strength":round(float(np.linalg.norm(z)/math.sqrt(len(z))),4)}
    names=list(summary); Z=np.array([[summary[c]["z_profile"][k] for k in FEATURE_NAMES] for c in names])
    def cos(a,b): na,nb=np.linalg.norm(a),np.linalg.norm(b); return float(a@b/(na*nb)) if na>0 and nb>0 else 0.0
    sim={a:{b:round(cos(Z[i],Z[j]),4) for j,b in enumerate(names)} for i,a in enumerate(names)}
    for i,c in enumerate(names):
        if c==control: continue
        peers=sorted(({"condition":b,"similarity":sim[c][b]} for b in names if b not in (c,control)),key=lambda x:-x["similarity"])
        refs=[]
        for m in MECHANISM_SIGNATURES:
            d=_reference_direction(m); idx=np.nonzero(d)[0]
            agree=[bool(np.sign(Z[i][k])==np.sign(d[k]) and abs(Z[i][k])>=z_match) for k in idx]
            refs.append({"mechanism":m,"agreement":round(sum(agree)/len(idx),4),
                         "matched_features":[FEATURE_NAMES[k] for k,a in zip(idx,agree) if a],
                         "contradicting_features":[FEATURE_NAMES[k] for k,a in zip(idx,agree) if not a and abs(Z[i][k])>=z_match],
                         "cosine":round(cos(Z[i],d),4)})
        refs.sort(key=lambda x:(-x["agreement"],-x["cosine"]))
        active=summary[c]["phenotype_strength"]>=1.0; top=refs[0]
        summary[c]["similar_conditions"]=peers
        summary[c]["reference_mechanism_matches"]=refs[:3]
        summary[c]["call"]=("inactive vs control" if not active else
                            f"resembles {top['mechanism']}" if top["agreement"]==1 else
                            f"partially resembles {top['mechanism']}" if top["agreement"]>=0.5 else
                            "active, unmatched phenotype (candidate novel mechanism)")
    qc=quality_control([per_well[w]["n_cells"] for w in per_well],[1.0]*len(per_well),[0.0])
    return {"wells":per_well,"conditions":summary,"similarity_matrix":sim,"control":control,
            "feature_names":FEATURE_NAMES,"qc":{"cell_count_cv":qc["cell_count_cv"],"low_cell_count_wells":[w for w,p in per_well.items() if p["low_cell_count"]]},
            "model_status":"classical image analysis (Otsu/distance-transform segmentation, GLCM texture, morphology); no trained model"}


def render_profile_heatmap(result, path=None, *, clip=5.0) -> str:
    """Render the condition x feature z-score heatmap from profile_wells() as SVG.

    Blue = decreased vs control, red = increased; returns the SVG text and writes it to ``path`` if given.
    """
    conds=result["conditions"]; names=list(conds); feats=result["feature_names"]
    if not names: raise ValueError("no conditions to render")
    cw,ch,left,top=14,18,170,175; W=left+cw*len(feats)+120; H=top+ch*len(names)+30
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="10">',
         f'<text x="{left}" y="14" font-size="12">Cell Painting profiles: robust z vs {result["control"]} (clipped at +/-{clip:g})</text>']
    for j,f in enumerate(feats):
        x=left+j*cw+cw/2; out.append(f'<text transform="translate({x},{top-4}) rotate(-60)">{f}</text>')
    for i,c in enumerate(names):
        y=top+i*ch; out.append(f'<text x="{left-6}" y="{y+ch*0.7}" text-anchor="end">{c}</text>')
        for j,f in enumerate(feats):
            z=max(-clip,min(clip,conds[c]["z_profile"][f])); t=abs(z)/clip
            r,g,b=(255,int(255*(1-t)),int(255*(1-t))) if z>0 else (int(255*(1-t)),int(255*(1-t)),255)
            out.append(f'<rect x="{left+j*cw}" y="{y}" width="{cw-1}" height="{ch-1}" fill="rgb({r},{g},{b})"><title>{c} {f}: z={conds[c]["z_profile"][f]}</title></rect>')
    out.append('</svg>'); svg="\n".join(out)
    if path:
        with open(path,"w") as fh: fh.write(svg)
    return svg
