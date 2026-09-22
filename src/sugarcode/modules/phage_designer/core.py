from __future__ import annotations

FIBER_SCAFFOLDS = {"T4_long": "gp37/gp38", "T7_tail": "gp17", "P2_tail": "G protein"}
RECEPTOR_BINDERS = {
    "OmpC": {"affinity_nM": 12, "scaffold": "T4_long"},
    "LamB": {"affinity_nM": 8, "scaffold": "T4_long"},
    "FhuA": {"affinity_nM": 25, "scaffold": "T7_tail"},
    "capsule_K1": {"affinity_nM": 45, "scaffold": "P2_tail"},
    "LPS_core": {"affinity_nM": 30, "scaffold": "P2_tail"},
}
LYSIN_DOMAINS = {"CHAP": {"activity": 0.9, "spectrum": "gram+"},
                 "glycosidase": {"activity": 0.7, "spectrum": "gram+/-"},
                 "amidase": {"activity": 0.8, "spectrum": "gram+/-"},
                 "endopeptidase": {"activity": 0.75, "spectrum": "gram+"}}


def design_fiber(target_receptor: str, host_pathogen: str = "Escherichia_coli") -> dict:
    """Swap tail fiber receptor-binding domain to retarget phage host range."""
    if target_receptor not in RECEPTOR_BINDERS:
        raise KeyError(f"no binder for {target_receptor}; have {sorted(RECEPTOR_BINDERS)}")
    b = RECEPTOR_BINDERS[target_receptor]
    adsorption = round(min(0.99, 0.55 + 12.0 / b["affinity_nM"]), 3)
    return {
        "target_receptor": target_receptor, "host_pathogen": host_pathogen,
        "scaffold": FIBER_SCAFFOLDS[b["scaffold"]],
        "predicted_binding_nM": b["affinity_nM"],
        "predicted_adsorption_rate": adsorption,
        "engineering": [f"PCR-amplify {b['scaffold']} fiber with {target_receptor}-binding tip domain",
                        "swap into phage genome via CRISPR-assisted recombineering",
                        "select on {host_pathogen} lawns expressing {target_receptor}"],
        "off_target_risk": "low" if b["affinity_nM"] < 30 else "moderate",
        "validation": ["plaque assay on receptor+ and receptor-knockout strains",
                       "adsorption kinetics (chloroform assay)",
                       "one-step growth curve on new host"],
    }


def design_lysin(gram_type: str = "gram+", domains: list[str] | None = None) -> dict:
    """Design a chimeric endolysin from catalytic + binding domains; tune potency."""
    domains = domains or ["CHAP", "amidase"]
    picked = [d for d in domains if d in LYSIN_DOMAINS]
    if not picked:
        raise ValueError(f"no valid domains; have {sorted(LYSIN_DOMAINS)}")
    spectrum_fit = {"gram+": {"CHAP": 1.0, "endopeptidase": 1.0, "amidase": 0.8, "glycosidase": 0.6},
                    "gram-": {"CHAP": 0.2, "endopeptidase": 0.2, "amidase": 0.9,
                              "glycosidase": 0.9}}
    fit = spectrum_fit.get(gram_type, spectrum_fit["gram+"])
    potency = round(sum(LYSIN_DOMAINS[d]["activity"] * fit[d] for d in picked) / len(picked), 3)
    outer_membrane_note = ("" if gram_type == "gram+" else
                           "gram- outer membrane blocks lysins - add membrane-penetrating "
                           "peptide (Artilysin) or co-administer with permeabilizer")
    return {
        "gram_type": gram_type, "domains": picked,
        "chimera": " + ".join(picked) + " | cell-wall binding domain",
        "predicted_potency": potency,
        "MIC_estimate_ug_mL": round(max(0.1, 8.0 * (1.1 - potency)), 2),
        "outer_membrane_strategy": outer_membrane_note or "not needed (gram+)",
        "validation": ["turbidity reduction assay", "MIC against clinical isolates panel",
                       "biofilm disruption (crystal violet)"],
    }

import math

def adsorption_kinetics(phage,bacteria,k_ads,time_min=60):
 bound=phage*bacteria/(bacteria+1/k_ads); remaining=phage-bound; return {'bound':bound,'free':remaining,'adsorbed_fraction':bound/phage,'time_min':time_min}
def host_range(receptor_profile,design):
 scores={strain:sum(float(expr.get(design['target_receptor'],0))*design['predicted_adsorption_rate'] for _ in [0]) for strain,expr in receptor_profile.items()}; return {'strain_scores':scores,'predicted_hosts':[s for s,v in scores.items() if v>.3]}
def escape_probability(mutation_rate,target_sites,population): return {'escape_probability':1-math.exp(-mutation_rate*target_sites*population),'expected_escape_variants':mutation_rate*target_sites*population}
def cocktail_design(phages,strains):
 cover={s:[p['target_receptor'] for p in phages if s in p.get('predicted_hosts',[])] for s in strains}; return {'coverage':cover,'covered_fraction':sum(bool(v) for v in cover.values())/max(1,len(strains)),'redundant_hosts':[s for s,v in cover.items() if len(v)>1]}
def phage_report(receptor,profiles):
 d=design_fiber(receptor); hr=host_range(profiles,d); return {**d,'host_range':hr,'escape':escape_probability(1e-8,1,1e8),'model_status':'Curated binder/kinetic heuristics; no trained host-range or clinical efficacy model. Engineering text is non-procedural concept only.'}
