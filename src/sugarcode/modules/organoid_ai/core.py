from __future__ import annotations
import math

ORGANOID_RECIPES = {
    "intestinal": {"factors": ["Wnt3a", "R-spondin", "Noggin", "EGF"],
                   "matrix": "Matrigel", "doubling_days": 2},
    "cerebral": {"factors": ["dual-SMAD inhibitors", "FGF2", "BDNF"],
                 "matrix": "Matrigel droplets", "doubling_days": 5},
    "hepatic": {"factors": ["HGF", "FGF10", "OSM", "dexamethasone"],
                "matrix": "Matrigel", "doubling_days": 4},
    "pancreatic": {"factors": ["FGF10", "Noggin", "R-spondin", "A83-01"],
                   "matrix": "Matrigel", "doubling_days": 3},
    "tumor": {"factors": ["EGF", "FGF2", "Noggin", "patient-specific"],
              "matrix": "Matrigel", "doubling_days": 3},
}


def design_organoid(tissue: str, patient_mutations: list[str] | None = None) -> dict:
    """Optimal growth conditions + media recipe + spatial expression map."""
    key = tissue.lower()
    if key not in ORGANOID_RECIPES:
        raise KeyError(f"unknown tissue {tissue!r}; have {sorted(ORGANOID_RECIPES)}")
    r = ORGANOID_RECIPES[key]
    spatial = _spatial_map(key, patient_mutations or [])
    return {
        "tissue": tissue,
        "media_recipe": {"base": "advanced DMEM/F12 + B27 + N2",
                         "factors": r["factors"], "matrix": r["matrix"],
                         "passage": "1:3 every 7-10 days by mechanical disruption"},
        "growth_conditions": {"temp_c": 37, "co2_pct": 5,
                              "doubling_days": r["doubling_days"]},
        "spatial_expression": spatial,
        "patient_mutations": patient_mutations or [],
        "quality_checks": ["morphology score at passage 2", "marker panel by IF",
                           "short tandem repeat match to patient tissue"],
    }


def _spatial_map(tissue: str, mutations: list[str]) -> dict:
    zones = {"intestinal": {"crypt": ["LGR5", "OLFM4"], "villus": ["VIL1", "ALPI"]},
             "cerebral": {"ventricular": ["PAX6", "SOX2"], "cortical": ["TBR1", "CTIP2"]},
             "hepatic": {"periportal": ["ALB", "CPS1"], "perivenous": ["CYP2E1", "GS"]},
             "pancreatic": {"duct": ["KRT19", "SOX9"], "acinar": ["AMY2A"]},
             "tumor": {"core": ["MKI67", "HIF1A"], "rim": ["KRT14"]}}
    return {"zones": zones.get(tissue, {}),
            "mutation_driven_zones": {m: "expanded proliferative zone" for m in mutations}}


def simulate_growth(tissue: str, days: int = 14, seed_cells: int = 5000) -> dict:
    """Logistic growth of the organoid population + size estimate."""
    r = ORGANOID_RECIPES.get(tissue.lower(), ORGANOID_RECIPES["intestinal"])
    lam = math.log(2) / r["doubling_days"]
    carrying = 5e6
    series = []
    for d in range(0, days + 1):
        n = carrying / (1 + (carrying / seed_cells - 1) * math.exp(-lam * d))
        series.append({"day": d, "cells": round(n),
                       "diameter_um": round(50 * (n / seed_cells) ** (1 / 3), 1)})
    return {"tissue": tissue, "trajectory": series,
            "final_cells": series[-1]["cells"],
            "note": "logistic model; necrotic core risk above ~500 um diameter"}


def drug_response(tissue: str, compounds: list[str], mutations: list[str] | None = None) -> dict:
    """Drug response on the organoid: IC50-style curves with mutation modifiers."""
    from ..cell_twin.core import DRUG_ACTIONS
    muts = set(mutations or [])
    out = {}
    for c in compounds:
        act = DRUG_ACTIONS.get(c, {"kill": 0.4, "resist_genes": []})
        resist = 0.4 if muts & set(act.get("resist_genes", [])) else 0.0
        ic50 = round(1.0 * (1 + 3 * resist), 3)
        doses = [0.03, 0.1, 0.3, 1, 3, 10]
        viability = [round(100 / (1 + (d / ic50) ** 1.5 * act["kill"]), 1) for d in doses]
        out[c] = {"ic50_uM": ic50, "doses_uM": doses, "viability_pct": viability,
                  "resistance_modifier": resist}
    return {"tissue": tissue, "mutations": sorted(muts), "responses": out,
            "most_effective": min(out, key=lambda c: out[c]["ic50_uM"]) if out else None}
