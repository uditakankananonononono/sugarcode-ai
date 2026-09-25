from __future__ import annotations
import math

TISSUES = {
    "skin": {"cells": ["keratinocytes", "fibroblasts"], "layers": 2,
             "modulus_kpa": 100, "vascular_need": 0.4},
    "cartilage": {"cells": ["chondrocytes"], "layers": 1,
                  "modulus_kpa": 800, "vascular_need": 0.0},
    "cardiac_patch": {"cells": ["cardiomyocytes", "endothelial", "fibroblasts"],
                      "layers": 3, "modulus_kpa": 30, "vascular_need": 0.9},
    "liver": {"cells": ["hepatocytes", "endothelial", "stellate"],
              "layers": 4, "modulus_kpa": 5, "vascular_need": 1.0},
    "bone": {"cells": ["osteoblasts", "endothelial"], "layers": 2,
             "modulus_kpa": 20000, "vascular_need": 0.7},
}
BIOINKS = {
    "gelma": {"modulus_kpa": (5, 100), "cell_friendly": 0.9, "printability": 0.8},
    "alginate": {"modulus_kpa": (20, 200), "cell_friendly": 0.6, "printability": 0.9},
    "collagen": {"modulus_kpa": (1, 30), "cell_friendly": 0.95, "printability": 0.5},
    "pegda": {"modulus_kpa": (50, 1000), "cell_friendly": 0.4, "printability": 0.85},
    "decell_ecm": {"modulus_kpa": (1, 50), "cell_friendly": 1.0, "printability": 0.6},
}


def _validate_size(size_mm) -> tuple:
    if len(size_mm) != 3 or any((not isinstance(x, (int, float))) or x <= 0 for x in size_mm):
        raise ValueError("size_mm must be three positive dimensions (x, y, z) in mm")
    return tuple(float(x) for x in size_mm)


def design_tissue(tissue: str, size_mm: tuple[float, float, float] = (10, 10, 2)) -> dict:
    """Full bioprinting strategy: cells, bioink, print parameters, mechanics."""
    size_mm = _validate_size(size_mm)
    key = tissue.lower()
    if key not in TISSUES:
        raise KeyError(f"unknown tissue {tissue!r}; have {sorted(TISSUES)}")
    t = TISSUES[key]
    ink = _pick_ink(t["modulus_kpa"])
    params = _print_params(ink, size_mm)
    mech = _mechanical_simulation(ink, t)
    vasc = _vascularization(t, size_mm)
    return {
        "tissue": tissue, "size_mm": size_mm,
        "cell_composition": t["cells"], "layers": t["layers"],
        "bioink": ink,
        "print_parameters": params,
        "mechanical_simulation": mech,
        "vascularization": vasc,
        "maturation": _maturation(key),
    }


def _pick_ink(target_kpa: float) -> dict:
    best = None
    for name, v in BIOINKS.items():
        lo, hi = v["modulus_kpa"]
        fit = 1.0 if lo <= target_kpa <= hi else 1 / (1 + abs(math.log10(target_kpa / max(hi, 1))))
        score = 0.5 * fit + 0.3 * v["cell_friendly"] + 0.2 * v["printability"]
        if best is None or score > best[1]:
            best = (name, score, v)
    return {"name": best[0], "score": round(best[1], 3), **best[2]}


def _print_params(ink: dict, size_mm: tuple) -> dict:
    return {"nozzle_um": 250 if ink["printability"] > 0.6 else 400,
            "pressure_kpa": round(80 / max(ink["printability"], 0.2), 1),
            "speed_mm_s": round(10 * ink["printability"], 1),
            "layer_height_um": 200,
            "n_layers": max(1, round(size_mm[2] * 1000 / 200)),
            "crosslinking": "UV 365nm 30s per layer" if ink["name"] in ("gelma", "pegda") else "ionic (CaCl2 100mM)"}


def _mechanical_simulation(ink: dict, tissue: dict) -> dict:
    lo, hi = ink["modulus_kpa"]
    achieved = (lo + hi) / 2
    strains = [0.05, 0.1, 0.2]
    stress = [round(achieved * s * 1.2, 1) for s in strains]  # neo-Hookean-ish
    return {
        "target_modulus_kpa": tissue["modulus_kpa"],
        "achievable_modulus_kpa": achieved,
        "match": lo <= tissue["modulus_kpa"] <= hi,
        "stress_strain": {"strain": strains, "stress_kpa": stress},
        "physiological_loading": "vascular pulsation 1 Hz 5% strain" if tissue["vascular_need"] > 0.5 else "static/compressive",
        "failure_strain_estimate": round(0.6 * ink["cell_friendly"] + 0.2, 2),
    }


def _vascularization(tissue: dict, size_mm: tuple) -> dict:
    need = tissue["vascular_need"]
    thickness = size_mm[2]
    diffusion_limit_mm = 0.2
    requires = need > 0.3 and thickness > diffusion_limit_mm
    return {
        "required": requires,
        "strategy": ("sacrificial Pluronic F127 channels + endothelial seeding"
                     if requires else "diffusion sufficient at this thickness"),
        "channel_spacing_um": 500 if requires else None,
        "perfusion": "microfluidic perfusion loop at 1 dyn/cm2 during maturation" if requires else None,
    }


def _maturation(tissue: str) -> list[str]:
    return ["day 1-3: viability check (Live/Dead), expect >80%",
            "week 1: marker expression panel",
            "week 2-4: functional maturation under physiological loading",
            "endpoint: histology + mechanical test + function assay"]


def calibrate_printing(tissue, ink_name=None, nozzle_um=250, target_fidelity=0.85):
    """Calibrate extrusion parameters and estimate structural fidelity."""
    key = tissue.lower()
    if key not in TISSUES:
        raise KeyError(f"unknown tissue {tissue!r}; have {sorted(TISSUES)}")
    if ink_name is None:
        ink = _pick_ink(TISSUES[key]["modulus_kpa"])
    elif ink_name not in BIOINKS:
        raise KeyError(f"unknown bioink {ink_name!r}; have {sorted(BIOINKS)}")
    else:
        ink = {"name": ink_name, **BIOINKS[ink_name]}
    if nozzle_um <= 0 or not 0 < target_fidelity <= 1:
        raise ValueError("nozzle_um must be positive and target_fidelity within (0, 1]")
    pressure = 80 / max(ink["printability"], .2) * (250 / nozzle_um)
    speed = 10 * ink["printability"] * (nozzle_um / 250) ** .5
    fidelity = min(.99, max(0.0, .55 + .35 * ink["printability"] - .0002 * abs(nozzle_um - 250)))
    return {"tissue": key, "bioink": ink["name"], "nozzle_um": nozzle_um,
            "pressure_kpa": round(pressure, 2), "speed_mm_s": round(speed, 2),
            "predicted_fidelity": round(fidelity, 3), "target_fidelity": target_fidelity,
            "target_met": fidelity >= target_fidelity,
            "calibration_note": "computational starting point; calibrate on the specific printer"}


def simulate_physiological_stress(tissue, cycles=1000, strain=0.05):
    """Estimate cyclic mechanical response and fatigue safety."""
    if cycles < 1 or not 0 < strain < 1:
        raise ValueError("cycles must be at least 1 and strain within (0, 1)")
    design = design_tissue(tissue)
    modulus = design["mechanical_simulation"]["achievable_modulus_kpa"]
    peak = modulus * strain * 1.2
    retained = max(.05, math.exp(-cycles * strain / 50000))
    failure = design["mechanical_simulation"]["failure_strain_estimate"]
    return {"tissue": tissue.lower(), "cycles": cycles, "applied_strain": strain,
            "peak_stress_kpa": round(peak, 4), "modulus_retention": round(retained, 4),
            "failure_strain_estimate": failure, "safety_factor": round(failure / strain, 3),
            "predicted_integrity": retained >= .8 and strain < failure,
            "model_status": "simplified computational prediction; mechanical testing required"}


def oxygen_profile(tissue, size_mm=(10,10,2), channel_spacing_um=None, points=11):
    """Predict a symmetric oxygen profile between vascular channels."""
    if points < 3:
        raise ValueError("points must be at least 3")
    key=tissue.lower()
    if key not in TISSUES:
        raise KeyError(f"unknown tissue {tissue!r}; have {sorted(TISSUES)}")
    size_mm=_validate_size(size_mm)
    vascular=_vascularization(TISSUES[key],size_mm)
    if channel_spacing_um is not None:
        spacing=channel_spacing_um
    else:
        spacing=vascular["channel_spacing_um"] or size_mm[2]*1000
    if spacing <= 0:
        raise ValueError("channel_spacing_um must be positive")
    distances=[spacing*i/(points-1) for i in range(points)]
    nearest=[min(x,spacing-x) for x in distances]
    oxygen=[max(0,1-(d/200)**2)*100 for d in nearest]
    return {"tissue":key,"channel_spacing_um":spacing,"distance_um":[round(x,2) for x in distances],
            "oxygen_percent":[round(x,2) for x in oxygen],"minimum_oxygen_percent":round(min(oxygen),2),
            "hypoxic":min(oxygen)<5,"recommended_max_spacing_um":math.floor(400*math.sqrt(0.95)*10)/10,  # largest spacing whose midpoint stays >= 5% oxygen in this model
            "model_status":"diffusion-only prediction; perfusion validation required"}


def viability_forecast(tissue, days=28, initial_viability=0.95, perfused=True):
    """Forecast cell viability during scaffold maturation."""
    if days < 1 or not 0 < initial_viability <= 1:
        raise ValueError("days must be positive and initial_viability within (0, 1]")
    key=tissue.lower()
    if key not in TISSUES:
        raise KeyError(f"unknown tissue {tissue!r}; have {sorted(TISSUES)}")
    need=TISSUES[key]["vascular_need"]
    decay=.006 + need*(.004 if perfused else .025)
    values=[round(initial_viability*math.exp(-decay*d),4) for d in range(days+1)]
    return {"tissue":key,"days":list(range(days+1)),"viability_fraction":values,
            "endpoint_viability":values[-1],"perfused":perfused,
            "functional_viability":values[-1]>=.7,
            "model_status":"computational forecast; confirm with Live/Dead assays"}


def drug_testing_plan(tissue, compounds, replicates=3):
    """Produce a randomized-ready in-vitro drug-testing layout."""
    if not compounds:
        raise ValueError("compounds must be a non-empty list")
    if replicates < 2:
        raise ValueError("replicates must be at least 2")
    design=design_tissue(tissue)
    groups=[{"compound":c,"replicate":r,"readouts":["viability","histology","tissue-specific function"]}
            for c in ["vehicle_control",*compounds] for r in range(1,replicates+1)]
    return {"tissue":tissue.lower(),"groups":groups,"sample_count":len(groups),
            "bioink":design["bioink"]["name"],"include_blinded_analysis":True,
            "limitations":["in-vitro response does not establish clinical efficacy","dose selection requires compound-specific evidence"]}
