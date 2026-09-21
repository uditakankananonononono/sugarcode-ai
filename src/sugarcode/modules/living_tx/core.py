from __future__ import annotations

CHASSIS = {
    "E_coli_Nissle": {"safety": 0.9, "engineering_ease": 0.95, "engraftment": 0.4},
    "Lactobacillus": {"safety": 0.95, "engineering_ease": 0.6, "engraftment": 0.7},
    "Bacteroides": {"safety": 0.85, "engineering_ease": 0.5, "engraftment": 0.9},
    "S_boulardii": {"safety": 0.9, "engineering_ease": 0.55, "engraftment": 0.3},
}
PAYLOADS = {
    "IL-22": {"indication": "IBD mucosal healing", "risk": 0.2},
    "IL-10": {"indication": "colitis", "risk": 0.15},
    "GLP-1": {"indication": "metabolic disease", "risk": 0.25},
    "phenylalanine_degradase": {"indication": "PKU", "risk": 0.1},
    "oxalate_decarboxylase": {"indication": "kidney stones", "risk": 0.1},
}


def design_living_therapeutic(indication_payload: str, chassis: str | None = None) -> dict:
    """Strain + genetic program for a living therapeutic, with community impact."""
    if indication_payload not in PAYLOADS:
        raise KeyError(f"unknown payload; have {sorted(PAYLOADS)}")
    pay = PAYLOADS[indication_payload]
    if chassis is None:
        chassis = max(CHASSIS, key=lambda c: 0.4 * CHASSIS[c]["safety"]
                      + 0.3 * CHASSIS[c]["engraftment"] + 0.3 * CHASSIS[c]["engineering_ease"])
    ch = CHASSIS[chassis]
    impact = _community_sim(chassis, indication_payload)
    success = round(0.35 * ch["engraftment"] + 0.35 * ch["safety"]
                    + 0.3 * (1 - pay["risk"]) - 0.1 * impact["disruption_index"], 3)
    return {
        "payload": indication_payload, "indication": pay["indication"],
        "chassis": chassis, "chassis_properties": ch,
        "genetic_program": {
            "expression": "inducible (anaerobic/food-trigger promoter)",
            "secretion": "Sec-tag for extracellular delivery",
            "containment": ["kill switch: arabinose-dependent toxin-antitoxin",
                            "auxotrophy for non-natural amino acid"],
        },
        "microbiome_impact": impact,
        "delivery_model": _delivery(pay),
        "predicted_clinical_success": success,
        "regulatory_path": "Live Biotherapeutic Product (FDA LBP guidance)",
    }


def _community_sim(chassis: str, payload: str) -> dict:
    """Simplified gut-community effect: engraftment displacement + niche overlap."""
    en = CHASSIS[chassis]["engraftment"]
    displacement = round(0.3 * en, 3)
    return {
        "predicted_engraftment_weeks": round(4 + 12 * en, 1),
        "resident_displacement_fraction": displacement,
        "disruption_index": round(displacement * (0.5 if chassis == "Bacteroides" else 1.0), 3),
        "beneficial_effects": _effects(payload),
        "monitoring": ["16S weekly during dosing", "payload biomarker in stool/serum"],
    }


def _effects(payload: str) -> list[str]:
    return {"IL-22": ["mucosal barrier strengthening"],
            "IL-10": ["reduced intestinal inflammation"],
            "GLP-1": ["improved glycemic response"],
            "phenylalanine_degradase": ["lower systemic phenylalanine"],
            "oxalate_decarboxylase": ["reduced urinary oxalate"]}[payload]


def _delivery(pay: dict) -> dict:
    return {"route": "oral, enteric capsule",
            "dose": "1e9-1e10 CFU daily x 8 weeks",
            "compound_delivery": "in situ secretion at mucosal surface"}
