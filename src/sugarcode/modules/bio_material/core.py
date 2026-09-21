from __future__ import annotations
from ..metabodesigner.core import design_pathway

MATERIALS = {
    "PHA": {"monomer": "3-hydroxybutyrate", "pathway_target": "PHB_polymer",
            "youngs_modulus_mpa": 3500, "tensile_mpa": 40, "biocompatible": True},
    "spider_silk": {"monomer": "protein (MaSp repeat)", "pathway_target": None,
                    "youngs_modulus_mpa": 10000, "tensile_mpa": 1100, "biocompatible": True},
    "bacterial_cellulose": {"monomer": "glucose", "pathway_target": None,
                            "youngs_modulus_mpa": 15000, "tensile_mpa": 200, "biocompatible": True},
    "PLA_bio": {"monomer": "lactate", "pathway_target": "lactate",
                "youngs_modulus_mpa": 3000, "tensile_mpa": 60, "biocompatible": True},
}


def design_biomaterial(material: str, application: str = "scaffold",
                       implant_site: str = "soft_tissue") -> dict:
    """Full design stack: production pathway, degradation curve, properties."""
    if material not in MATERIALS:
        raise KeyError(f"unknown material {material!r}; have {sorted(MATERIALS)}")
    m = MATERIALS[material]
    pathway = None
    if m["pathway_target"]:
        pathway = design_pathway(m["pathway_target"])
    degradation = _degradation(material, implant_site)
    props = _properties(material, application)
    return {
        "material": material, "application": application,
        "monomer": m["monomer"],
        "production_pathway": pathway,
        "degradation": degradation,
        "predicted_properties": props,
        "structure_function": _structure_function(material),
        "fabrication": _fabrication(material, application),
    }


def _degradation(material: str, site: str) -> dict:
    """First-order hydrolytic/enzymatic degradation model under physiology."""
    rates = {"PHA": 0.02, "spider_silk": 0.005, "bacterial_cellulose": 0.001,
             "PLA_bio": 0.03}  # per day at 37C
    site_factor = {"soft_tissue": 1.2, "bone": 0.8, "blood": 1.5, "skin": 1.0}
    k = rates[material] * site_factor.get(site, 1.0)
    days = list(range(0, 181, 15))
    remaining = [round(100 * (0.5 ** (d * k)), 1) for d in days]
    half_life = round(0.693 / k, 1)
    return {"model": "first-order", "k_per_day": round(k, 4),
            "half_life_days": half_life, "site": site,
            "days": days, "mass_remaining_pct": remaining}


def _properties(material: str, application: str) -> dict:
    m = MATERIALS[material]
    app_need = {"scaffold": {"modulus_min": 100, "porosity": 0.7},
                "suture": {"modulus_min": 1000, "porosity": 0.0},
                "drug_depot": {"modulus_min": 10, "porosity": 0.4}}
    need = app_need.get(application, app_need["scaffold"])
    return {
        "youngs_modulus_mpa": m["youngs_modulus_mpa"],
        "tensile_strength_mpa": m["tensile_mpa"],
        "biocompatible": m["biocompatible"],
        "meets_application_modulus": m["youngs_modulus_mpa"] >= need["modulus_min"],
        "recommended_porosity": need["porosity"],
    }


def _structure_function(material: str) -> str:
    notes = {
        "PHA": "Semicrystalline polyester; crystallinity sets stiffness vs toughness; 3HB fraction controls degradation.",
        "spider_silk": "Beta-sheet nanocrystals in amorphous glycine-rich matrix: strength from crystals, elasticity from matrix.",
        "bacterial_cellulose": "Ribbon-like microfibrils, high crystallinity, excellent water retention for wound contact.",
        "PLA_bio": "Stereocomplexation of L/D lactide tunes melting point and degradation rate.",
    }
    return notes[material]


def _fabrication(material: str, application: str) -> list[str]:
    base = {"PHA": ["biosynthesize in R. eutropha", "solvent cast or electrospin"],
            "spider_silk": ["express MaSp in E. coli/yeast", "wet-spin fibers", "post-draw 3x"],
            "bacterial_cellulose": ["culture K. xylinus static", "harvest pellicle", "purify with NaOH"],
            "PLA_bio": ["ferment lactate", "chemical polymerization", "melt extrude"]}
    steps = base[material]
    if application == "scaffold":
        steps.append("salt-leach or 3D print for porosity")
    return steps
