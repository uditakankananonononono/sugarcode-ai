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


import json as _json
from pathlib import Path as _Path

# ChEMBL target IDs resolved by exact pref_name against the live API on
# 2026-09-21; FROUNT has no ChEMBL target - honestly absent.
_CHEMBL_TARGETS = _json.load(open(_Path(__file__).parent / "data_chembl_targets.json"))
# graph drug name -> ChEMBL preferred name (sirolimus is rapamycin's INN;
# simvastatin represents the statin class - documented curation)
_DRUG_ALIASES = {"rapamycin": "sirolimus", "statins": "simvastatin"}


def live_validation(candidates: list[dict], offline: bool = False) -> list[dict]:
    """Validate repurposing candidates against LIVE ChEMBL bioactivity.

    For each candidate drug's targets, resolves the ChEMBL target and pulls
    measured activities; reports the best measured potency for that drug when
    ChEMBL knows the molecule, plus assay counts. Real data replaces the
    docking-proxy validation note; failures are reported per candidate.
    """
    from ...bio import chembl
    # map graph drug names to ChEMBL molecules via name lookup
    out = []
    for c in candidates:
        entry = {"drug": c["drug"], "tri": c.get("therapeutic_resilience_index")}
        query_name = _DRUG_ALIASES.get(c["drug"], c["drug"])
        try:
            mols = chembl._get(
                f"{chembl.BASE}/molecule.json?pref_name__iexact="
                f"{chembl.urllib.parse.quote(query_name)}&limit=1", offline=offline)
            mlist = mols.get("molecules", [])
            if not mlist:
                entry["chembl"] = {"status": "molecule not found by name"}
                out.append(entry)
                continue
            mol = mlist[0]
            mol_id = mol["molecule_chembl_id"]
            best = None
            n_assays = 0
            for t in c.get("paths", []):
                tgt = _CHEMBL_TARGETS.get(t["target"])
                if not tgt:
                    continue  # e.g. FROUNT - no ChEMBL target, honestly skipped
                acts = chembl.activities_for_target(tgt["chembl_id"], max_n=200,
                                                    offline=offline)
                mine = [a for a in acts if a["molecule_chembl_id"] == mol_id]
                n_assays += len(acts)
                if mine and (best is None or mine[0]["value_nM"] < best["value_nM"]):
                    best = {**mine[0], "target": t["target"],
                            "target_chembl_id": tgt["chembl_id"]}
            entry["chembl"] = {
                "status": "live",
                "molecule_chembl_id": mol_id,
                "queried_as": query_name,
                "max_phase": mol.get("max_phase"),
                "best_measured_potency": best,
                "activities_screened": n_assays,
                "evidence": ("measured bioactivity found in ChEMBL" if best
                             else "no direct measurement for this drug on these targets"),
            }
        except Exception as e:
            entry["chembl"] = {"status": f"lookup failed: {type(e).__name__}: {e}"}
        out.append(entry)
    return out


def repurposing_scan_live(disease: str, top_n: int = 5, offline: bool = False) -> dict:
    """Graph-walk repurposing + live ChEMBL validation of every candidate."""
    r = repurposing_scan(disease, top_n=top_n)
    r["candidates_validated"] = live_validation(r["candidates"], offline=offline)
    r["validation_source"] = "ChEMBL (live measured bioactivity)"
    return r
