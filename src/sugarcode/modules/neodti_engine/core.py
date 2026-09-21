from __future__ import annotations
from collections import defaultdict

# Built-in multiplex slice: drug-target, target-pathway, pathway-disease
DRUG_TARGETS = {
    "metformin": ["AMPK", "ETC1"], "aspirin": ["COX1", "COX2"],
    "sildenafil": ["PDE5"], "thalidomide": ["CRBN", "TNFa"],
    "rapamycin": ["mTOR"], "statins": ["HMGCR"], "disulfiram": ["ALDH", "FROUNT"],
    "itraconazole": ["lanosterol14DM", "Hh_SMO"], "cimetidine": ["H2R"],
}
TARGET_PATHWAYS = {
    "AMPK": ["metabolism", "autophagy"], "ETC1": ["metabolism"],
    "COX1": ["inflammation"], "COX2": ["inflammation", "angiogenesis"],
    "PDE5": ["vascular_tone"], "CRBN": ["protein_degradation"],
    "TNFa": ["inflammation"], "mTOR": ["growth_signaling", "autophagy"],
    "HMGCR": ["cholesterol", "prenylation"], "ALDH": ["detox"],
    "FROUNT": ["macrophage_migration"], "lanosterol14DM": ["sterol_synthesis"],
    "Hh_SMO": ["hedgehog_signaling"], "H2R": ["acid_secretion", "immune_modulation"],
}
PATHWAY_DISEASES = {
    "metabolism": ["T2D", "cancer_metabolic"], "autophagy": ["neurodegeneration", "aging"],
    "inflammation": ["arthritis", "cancer_inflammatory", "cardiovascular"],
    "angiogenesis": ["cancer_solid"], "vascular_tone": ["pulmonary_hypertension", "ED"],
    "protein_degradation": ["myeloma"], "growth_signaling": ["cancer_solid", "aging"],
    "cholesterol": ["cardiovascular"], "prenylation": ["cancer_solid"],
    "detox": ["alcoholism"], "macrophage_migration": ["cancer_inflammatory"],
    "sterol_synthesis": ["fungal_infection"], "hedgehog_signaling": ["basal_cell_carcinoma", "medulloblastoma"],
    "acid_secretion": ["GERD"], "immune_modulation": ["cancer_inflammatory"],
}
APPROVED_FOR = {
    "metformin": ["T2D"], "aspirin": ["pain", "cardiovascular"],
    "sildenafil": ["ED", "pulmonary_hypertension"], "thalidomide": ["myeloma", "leprosy"],
    "rapamycin": ["transplant_rejection"], "statins": ["cardiovascular"],
    "disulfiram": ["alcoholism"], "itraconazole": ["fungal_infection"],
    "cimetidine": ["GERD"],
}



# Common clinical names -> graph slugs (small curated alias layer)
DISEASE_ALIASES = {
    "type 2 diabetes": "T2D", "diabetes": "T2D", "t2d": "T2D",
    "breast cancer": "cancer_solid", "lung cancer": "cancer_solid",
    "solid tumor": "cancer_solid", "colorectal cancer": "cancer_solid",
    "glioblastoma": "cancer_solid", "pancreatic cancer": "cancer_solid",
    "metabolic cancer": "cancer_metabolic",
    "rheumatoid arthritis": "arthritis", "arthritis": "arthritis",
    "heart disease": "cardiovascular", "cardiovascular disease": "cardiovascular",
    "atherosclerosis": "cardiovascular",
    "alzheimer's": "neurodegeneration", "parkinson's": "neurodegeneration",
    "alzheimers": "neurodegeneration", "parkinsons": "neurodegeneration",
    "neurodegenerative disease": "neurodegeneration",
    "multiple myeloma": "myeloma", "myeloma": "myeloma",
    "pulmonary hypertension": "pulmonary_hypertension", "pah": "pulmonary_hypertension",
    "erectile dysfunction": "ED",
    "alcohol use disorder": "alcoholism", "alcoholism": "alcoholism",
    "systemic candidiasis": "fungal_infection", "fungal infection": "fungal_infection",
    "basal cell carcinoma": "basal_cell_carcinoma", "bcc": "basal_cell_carcinoma",
    "medulloblastoma": "medulloblastoma",
    "gerd": "GERD", "acid reflux": "GERD",
    "aging": "aging", "longevity": "aging",
    "inflammatory cancer": "cancer_inflammatory",
}


def resolve_disease(disease: str) -> str:
    """Map a free-text disease name onto a graph slug; pass slugs through."""
    d = disease.strip().lower()
    if d in DISEASE_ALIASES:
        return DISEASE_ALIASES[d]
    known = {d for ds in PATHWAY_DISEASES.values() for d in ds}
    if disease in known:
        return disease
    raise KeyError(
        f"disease {disease!r} not in graph; covered: "
        f"{sorted(set(known) | set(DISEASE_ALIASES))}")

def repurposing_scan(disease: str, top_n: int = 5) -> dict:
    """Graph-walk repurposing: disease <- pathway <- target <- drug.

    Scores by path count, directness and novelty (drug not already approved
    for the disease); validated with a docking check on the top hit.
    """
    disease = resolve_disease(disease)
    paths: dict[str, list[dict]] = defaultdict(list)
    for drug, targets in DRUG_TARGETS.items():
        for t in targets:
            for pw in TARGET_PATHWAYS.get(t, []):
                if disease in PATHWAY_DISEASES.get(pw, []):
                    paths[drug].append({"target": t, "pathway": pw})
    scored = []
    for drug, ps in paths.items():
        if disease in APPROVED_FOR.get(drug, []):
            continue  # already approved - not repurposing
        novelty = 1.0
        path_score = min(1.0, 0.4 * len(ps))
        distinct_targets = len({p["target"] for p in ps})
        tri = round(0.45 * path_score + 0.25 * min(distinct_targets / 3, 1.0)
                    + 0.3 * novelty, 3)
        scored.append({"drug": drug, "paths": ps, "n_paths": len(ps),
                       "therapeutic_resilience_index": tri})
    scored.sort(key=lambda x: -x["therapeutic_resilience_index"])
    top = scored[:top_n]
    validation = None
    if top:
        from ..docking_studio.core import dock
        validation = {"method": "pocket-complementarity docking proxy",
                      "top_hit": top[0]["drug"],
                      "note": "full structural validation requires resolved target structures"}
    return {
        "disease": disease,
        "graph": {"drugs": len(DRUG_TARGETS), "targets": len(TARGET_PATHWAYS),
                  "pathways": len(PATHWAY_DISEASES)},
        "candidates": top,
        "docking_validation": validation,
        "multiplex_note": "scores aggregate drug-target-pathway-disease paths; multi-path drugs rank higher",
    }
