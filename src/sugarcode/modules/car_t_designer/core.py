from __future__ import annotations

ANTIGENS = {
    "CD19": {"tumor": "B-ALL/lymphoma", "normal_expression": ["B cells"], "validated": True},
    "BCMA": {"tumor": "multiple myeloma", "normal_expression": ["plasma cells"], "validated": True},
    "HER2": {"tumor": "breast/gastric", "normal_expression": ["epithelia", "cardiac"], "validated": True},
    "GD2": {"tumor": "neuroblastoma", "normal_expression": ["neurons"], "validated": True},
    "GPC3": {"tumor": "hepatocellular", "normal_expression": [], "validated": False},
    "CLDN18.2": {"tumor": "gastric/pancreatic", "normal_expression": ["gastric mucosa"], "validated": False},
}
SCFV = {"FMC63": "CD19", "C11D5.3": "BCMA", "4D5": "HER2", "14G2a": "GD2",
        "GC33": "GPC3", "generic_high_affinity": None}
COSTIM = {"CD28": {"expansion": 0.9, "persistence": 0.4, "exhaustion": 0.7},
          "4-1BB": {"expansion": 0.6, "persistence": 0.9, "exhaustion": 0.3}}
HINGES = ["CD8a", "IgG4_short", "IgG4_long"]


def design_car(antigen: str, indication: str | None = None) -> dict:
    """Optimize a CAR construct for an antigen: scFv, hinge, costim, safety."""
    if antigen not in ANTIGENS:
        raise KeyError(f"unknown antigen {antigen!r}; have {sorted(ANTIGENS)}")
    ag = ANTIGENS[antigen]
    scfv = next((k for k, v in SCFV.items() if v == antigen), "generic_high_affinity")
    # 4-1BB favored when normal-tissue expression requires persistence caution
    on_target_off_tumor = len(ag["normal_expression"]) > 0
    costim = "4-1BB" if on_target_off_tumor else "CD28"
    c = COSTIM[costim]
    tox = _toxicity(ag, costim)
    return {
        "antigen": antigen, "tumor": ag["tumor"],
        "construct": {
            "scfv": scfv, "hinge": "CD8a" if costim == "4-1BB" else "IgG4_short",
            "costimulatory": costim, "activation": "CD3zeta",
            "architecture": f"{scfv}-scFv / hinge / TM / {costim} / CD3z",
        },
        "safety_switches": (["iCasp9 suicide switch", "truncated EGFR depletion marker"]
                            if on_target_off_tumor else ["truncated EGFR depletion marker"]),
        "toxicity_prediction": tox,
        "trial_simulation": _trial(c, tox),
        "manufacturing": ["leukapheresis", "lentiviral transduction MOI 3",
                          "7-10 day expansion with IL-7/IL-15", "release: >70% CAR+, viability >80%"],
        "rationale": (f"{costim} chosen for "
                      + ("persistence and lower exhaustion given on-target/off-tumor risk"
                         if on_target_off_tumor else "rapid expansion against low-risk target")),
    }


def _toxicity(ag: dict, costim: str) -> dict:
    crs = 0.3 + 0.2 * COSTIM[costim]["expansion"]
    ot = 0.15 * len(ag["normal_expression"])
    neuro = 0.1 if costim == "CD28" else 0.05
    return {"crs_grade2plus_risk": round(min(crs, 0.9), 2),
            "on_target_off_tumor_risk": round(min(ot, 0.9), 2),
            "neurotoxicity_risk": neuro,
            "monitoring": ["daily cytokines week 1", "tocilizumab on standby"]}


def _trial(costim: dict, tox: dict) -> dict:
    months = list(range(0, 13, 3))
    persistence = [round(costim["persistence"] * (0.85 ** m), 3) for m in months]
    response = round(0.5 + 0.3 * costim["expansion"] - 0.2 * tox["crs_grade2plus_risk"], 2)
    return {"months": months, "car_persistence_fraction": persistence,
            "predicted_overall_response": response,
            "readouts": ["MRD negativity", "CAR copy number", "cytokine panel"]}
