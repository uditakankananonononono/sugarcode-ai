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
    base = MECHANISM_SIGNATURES.get(mechanism, {})
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
        dot = sum(va[k] * vb[k] for k in keys)
        na = math.sqrt(sum(va[k] ** 2 for k in keys))
        nb = math.sqrt(sum(vb[k] ** 2 for k in keys))
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
 q=np.array(list(query['signature_vector'].values())); rows=[]
 for r in references:
  v=np.array(list(r['signature_vector'].values())); sim=float(q@v/(np.linalg.norm(q)*np.linalg.norm(v))); rows.append({'mechanism':r['mechanism'],'similarity':sim})
 return sorted(rows,key=lambda x:-x['similarity'])
def concentration_trajectory(mechanism,doses,hours): return {'profiles':[profile_perturbation(mechanism,d,h) for d in doses for h in hours]}
def cellpainting_report(profiles,controls):
 matrix=[list(x['signature_vector'].values()) for x in profiles]; return {'comparison':compare_profiles(profiles),'normalized':plate_normalize(matrix,controls),'mechanism_matches':[nearest_mechanism(x,profiles)[:3] for x in profiles],'model_status':'Hand-specified morphology signatures and transparent statistics; no image segmentation or trained morphology model.'}
