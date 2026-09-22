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

import math
import numpy as np
from scipy.integrate import solve_ivp

def polymerization_kinetics(monomer0=1,initiator=.01,kp=1,kt=.1,hours=10):
 def rhs(t,y): m,r,p=y; rate=kp*m*r; return [-rate,-2*kt*r*r,rate]
 t=np.linspace(0,hours,101); s=solve_ivp(rhs,(0,hours),[monomer0,initiator,0],t_eval=t,rtol=1e-8,atol=1e-10); return {'time_h':t.tolist(),'monomer':s.y[0].tolist(),'radicals':s.y[1].tolist(),'polymer':s.y[2].tolist(),'conversion':float(1-s.y[0,-1]/monomer0)}
def network_mechanics(crosslink_density,temperature_k=310,porosity=0):
 R=8.314; shear=crosslink_density*R*temperature_k/1e6; young=3*shear*(1-porosity)**2; return {'shear_modulus_mpa':shear,'youngs_modulus_mpa':young,'mesh_size_relative':1/math.sqrt(max(crosslink_density,1e-12)),'porosity':porosity}
def swelling_equilibrium(crosslink_density,solvent_quality=.5,ionic_strength=.15):
 q=1+solvent_quality*10/(1+crosslink_density/100)/(1+ionic_strength); return {'swelling_ratio':q,'water_fraction':1-1/q,'ionic_strength_m':ionic_strength}
def degradation_multimode(initial_mass=100,days=180,hydrolysis=.01,enzyme=.005,oxidation=.002):
 t=np.linspace(0,days,181); k=hydrolysis+enzyme+oxidation; mass=initial_mass*np.exp(-k*t); return {'days':t.tolist(),'mass':mass.tolist(),'half_life_days':math.log(2)/k,'mode_contributions':{'hydrolysis':hydrolysis/k,'enzyme':enzyme/k,'oxidation':oxidation/k}}
def diffusion_gradient(diffusivity=1e-6,degradation=.01,length_mm=1,steps=50):
 x=np.linspace(0,length_mm,steps); c=np.cosh(np.sqrt(degradation/diffusivity)*(length_mm-x))/np.cosh(np.sqrt(degradation/diffusivity)*length_mm); return {'position_mm':x.tolist(),'relative_concentration':c.tolist(),'penetration_depth_mm':math.sqrt(diffusivity/degradation)}
def cell_material_interface(stiffness_mpa,ligand_density=.5,immune_signal=.1):
 adhesion=ligand_density/(.2+ligand_density); mech=math.exp(-((math.log10(max(stiffness_mpa,1e-6))-1)/2)**2); return {'adhesion_probability':adhesion,'mechanotransduction':mech,'differentiation_bias':{'soft':1-mech,'stiff':mech},'immune_risk':min(1,immune_signal*(1+.2*stiffness_mpa/100))}
def rheology(shear_rates,yield_stress=10,consistency=5,index=.5):
 s=np.asarray(shear_rates,float); stress=yield_stress+consistency*s**index; return {'shear_rate':s.tolist(),'stress_pa':stress.tolist(),'viscosity_pa_s':(stress/np.maximum(s,1e-9)).tolist(),'shear_thinning':index<1}
def fabrication_resolution(nozzle_um,viscosity,gel_time_s):
 fidelity=math.exp(-abs(viscosity-5)/10)*min(1,gel_time_s/5); return {'resolution_um':nozzle_um*(1+.3/fidelity),'fidelity':fidelity,'printable':fidelity>.4}
def material_report(material,application='scaffold'):
 base=design_biomaterial(material,application); p=base['predicted_properties']; mech=network_mechanics(500,p['youngs_modulus_mpa']/3000*.2); return {**base,'polymerization':polymerization_kinetics(),'network_mechanics':mech,'swelling':swelling_equilibrium(500),'multimode_degradation':degradation_multimode(),'cell_interface':cell_material_interface(p['youngs_modulus_mpa']), 'rheology':rheology([1,10,100]),'model_status':'Explicit polymer, transport and mechanics equations; no generative AI/MD/FBA model and no synthesis-ready protocol.'}
def material_diagnostics(r):
 p=r['predicted_properties']; n=r['network_mechanics']; s=r['swelling']; d=r['multimode_degradation']; c=r['cell_interface']; return {'nominal_modulus':float(p['youngs_modulus_mpa']),'tensile_strength':float(p['tensile_strength_mpa']),'porosity':p['recommended_porosity'],'network_modulus':n['youngs_modulus_mpa'],'mesh_size':n['mesh_size_relative'],'swelling_ratio':s['swelling_ratio'],'water_fraction':s['water_fraction'],'degradation_half_life':d['half_life_days'],'adhesion_probability':c['adhesion_probability'],'mechanotransduction':c['mechanotransduction'],'immune_risk':c['immune_risk'],'polymer_conversion':r['polymerization']['conversion']}
