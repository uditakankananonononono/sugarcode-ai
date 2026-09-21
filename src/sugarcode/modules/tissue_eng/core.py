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


def design_tissue(tissue: str, size_mm: tuple[float, float, float] = (10, 10, 2)) -> dict:
    """Full bioprinting strategy: cells, bioink, print parameters, mechanics."""
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
