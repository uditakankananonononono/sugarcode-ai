from __future__ import annotations
import math
import random

# fragment library: (smiles, heavy_atoms, logp_contrib, hbd, hba, rotatable)
FRAGMENTS = {
    "benzene": ("c1ccccc1", 6, 1.7, 0, 0, 0),
    "pyridine": ("c1ccncc1", 6, 0.9, 0, 1, 0),
    "hydroxyl": ("O", 1, -1.0, 1, 1, 1),
    "amine": ("N", 1, -0.6, 1, 1, 1),
    "carboxyl": ("C(=O)O", 3, -0.3, 1, 2, 1),
    "amide": ("C(=O)N", 3, -0.8, 1, 2, 1),
    "methyl": ("C", 1, 0.5, 0, 0, 0),
    "ethyl_link": ("CC", 2, 1.0, 0, 0, 1),
    "fluorine": ("F", 1, 0.3, 0, 0, 0),
    "sulfonamide": ("S(=O)(=O)N", 5, -0.5, 1, 3, 1),
    "imidazole": ("c1c[nH]cn1", 5, 0.1, 1, 2, 0),
    "piperazine": ("C1CNCCN1", 6, -0.2, 2, 2, 0),
}
CYP_RISK_FRAGMENTS = {"aniline": 0.4, "benzene": 0.2, "imidazole": 0.5}
HERG_RISK = lambda logp, hbd: min(1.0, max(0.0, 0.15 * logp - 0.1 * hbd))  # lipophilic bases


def score_molecule(fragments: list[str]) -> dict:
    """ADMET profile from fragment composition (Crippen-style additivity)."""
    for f in fragments:
        if f not in FRAGMENTS:
            raise KeyError(f"unknown fragment {f!r}; have {sorted(FRAGMENTS)}")
    atoms = sum(FRAGMENTS[f][1] for f in fragments)
    logp = round(sum(FRAGMENTS[f][2] for f in fragments), 2)
    hbd = sum(FRAGMENTS[f][3] for f in fragments)
    hba = sum(FRAGMENTS[f][4] for f in fragments)
    rot = sum(FRAGMENTS[f][5] for f in fragments)
    mw = round(atoms * 13.5 + hbd * 8, 1)
    # aqueous solubility logS (Yalkowsky-style general solubility estimate)
    logS = round(0.5 - logp * 1.0 - 0.01 * (mw - 200) / 50, 2)
    lipinski = sum([mw <= 500, logp <= 5, hbd <= 5, hba <= 10])
    sa = round(max(1.0, 10.0 - rot * 0.4 - len(set(fragments)) * 0.5), 1)  # synthetic accessibility proxy
    return {
        "fragments": fragments, "mw": mw, "logP": logp, "logS": logS,
        "hbd": hbd, "hba": hba, "rotatable": rot,
        "lipinski_violations": 4 - lipinski,
        "cyp_risk": round(sum(CYP_RISK_FRAGMENTS.get(f, 0.05) for f in fragments) / len(fragments), 2),
        "herg_risk": round(HERG_RISK(logp, hbd), 2),
        "synthetic_accessibility": sa,
        "potency_prior": round(max(0.0, 0.5 + 0.1 * (hba - rot)), 2),
    }


def _objectives(m: dict, target_logp: float) -> dict:
    return {
        "potency": m["potency_prior"],
        "solubility": max(0.0, 1.0 + m["logS"] / 4),
        "safety": 1.0 - max(m["cyp_risk"], m["herg_risk"]),
        "logp_fit": max(0.0, 1.0 - abs(m["logP"] - target_logp) / 4),
        "feasibility": max(0.0, 1.0 - (m["synthetic_accessibility"] - 1) / 9),
    }


def pareto_front(candidates: list[dict]) -> list[dict]:
    """Non-dominated subset across objective vectors."""
    def dominates(a, b):
        oa, ob = a["objectives"], b["objectives"]
        return (all(oa[k] >= ob[k] for k in oa) and any(oa[k] > ob[k] for k in oa))
    return [c for c in candidates if not any(dominates(o, c) for o in candidates if o is not c)]


def generate(n: int = 12, target_logp: float = 2.5, seed: int = 42) -> dict:
    """Assemble candidate molecules from fragments, score ADMET, keep Pareto front."""
    rng = random.Random(seed)
    rings = [f for f in FRAGMENTS if FRAGMENTS[f][5] == 0 and FRAGMENTS[f][1] >= 5]
    groups = [f for f in FRAGMENTS if f not in rings]
    cands = []
    for _ in range(n):
        frag = [rng.choice(rings)] + [rng.choice(groups) for _ in range(rng.randint(1, 3))]
        m = score_molecule(frag)
        m["objectives"] = _objectives(m, target_logp)
        m["composite"] = round(sum(m["objectives"].values()) / 5, 3)
        cands.append(m)
    front = pareto_front(cands)
    for c in front:
        c["retrosynthesis"] = _retro(c["fragments"])
    return {
        "generated": n, "pareto_size": len(front),
        "pareto_front": sorted(front, key=lambda c: -c["composite"]),
        "target_logp": target_logp,
        "note": ("fragment-additive ADMET (Crippen-style LogP, Yalkowsky logS); "
                 "objective vector Pareto-filtered - trade-offs explicit, not blended"),
    }


def _retro(fragments: list[str]) -> list[dict]:
    steps = []
    for i, f in enumerate(fragments[1:], 1):
        steps.append({"step": i, "disconnection": f"remove {f}",
                      "reaction": "amide coupling" if f in ("amide", "carboxyl", "amine")
                      else "cross-coupling" if f in ("benzene", "pyridine", "imidazole")
                      else "alkylation"})
    return steps


def similarity_check(smiles: str, cutoff: int = 80, limit: int = 10,
                     offline: bool = False) -> dict:
    """Check a designed molecule against live ChEMBL: nearest known compounds
    (server-side Tanimoto), closest approved drug, and an honest novelty call.
    Failures are reported, never hidden."""
    from ...bio import chembl
    try:
        hits = chembl.similarity_search(smiles, cutoff=cutoff, limit=limit, offline=offline)
    except Exception as e:
        return {"smiles": smiles, "status": f"lookup failed: {type(e).__name__}: {e}",
                "neighbors": [], "novelty": "unknown"}
    if not hits:
        return {"smiles": smiles, "status": "ok", "neighbors": [],
                "novelty": f"no known molecule >= {cutoff}% similar in ChEMBL (novel scaffold space)",
                "closest": None}
    closest = hits[0]
    approved = [h for h in hits if (h.get("max_phase") or 0) and h["max_phase"] >= 3]
    novelty = ("close analog of known compounds" if closest["similarity"] >= 90
               else "related to known chemotypes" if closest["similarity"] >= 80
               else "novel at cutoff")
    return {"smiles": smiles, "status": "ok", "cutoff": cutoff, "neighbors": hits,
            "closest": {"chembl_id": closest["chembl_id"], "pref_name": closest["pref_name"],
                        "similarity": closest["similarity"], "max_phase": closest["max_phase"]},
            "approved_neighbors": [{"chembl_id": h["chembl_id"], "pref_name": h["pref_name"],
                                    "similarity": h["similarity"], "max_phase": h["max_phase"]}
                                   for h in approved],
            "novelty": novelty}

# Explicit graph/3D/physics surrogates. No trained generative or predictive
# model is bundled, and outputs are not clinically validated.
import json
import numpy as np

def molecular_graph(fragments):
    for f in fragments:
        if f not in FRAGMENTS: raise KeyError(f"unknown fragment {f!r}")
    nodes=[]; edges=[]; atom=0
    for index,f in enumerate(fragments):
        count=FRAGMENTS[f][1]; start=atom
        for i in range(count): nodes.append({"id":atom,"fragment":f,"element":"N" if 'N' in FRAGMENTS[f][0] and i==0 else "O" if 'O' in FRAGMENTS[f][0] and i==0 else "C"}); atom+=1
        for i in range(start,atom-1): edges.append({"source":i,"target":i+1,"bond_order":1})
        if index and start>0: edges.append({"source":start-1,"target":start,"bond_order":1})
    return {"nodes":nodes,"edges":edges}

def conformer_ensemble(fragments,n=20,seed=0):
    if n<1: raise ValueError("n must be >=1")
    graph=molecular_graph(fragments); rng=np.random.default_rng(seed); conformers=[]
    for i in range(n):
        coords=np.cumsum(rng.normal(0,1,(len(graph['nodes']),3)),axis=0); bond=np.diff(coords,axis=0); strain=float(np.mean((np.linalg.norm(bond,axis=1)-1.5)**2)) if len(coords)>1 else 0.; rg=float(np.sqrt(np.mean(np.sum((coords-coords.mean(0))**2,axis=1)))); conformers.append({"id":i,"energy_kcal_mol":strain,"radius_gyration":rg,"coordinates":coords.tolist()})
    conformers.sort(key=lambda x:x['energy_kcal_mol']); weights=np.exp(-np.array([x['energy_kcal_mol'] for x in conformers])/.593); weights/=weights.sum()
    for c,w in zip(conformers,weights): c['boltzmann_weight']=float(w)
    return conformers

def _applicability_uncertainty(fragments):
    profile = score_molecule(fragments)
    diversity = len(set(fragments)) / max(1, len(fragments))
    size_extrapolation = max(0.0, profile["mw"] - 350.0) / 350.0
    unusual = sum(f in ("sulfonamide", "piperazine", "imidazole") for f in fragments) / len(fragments)
    return 0.06 + 0.10 * diversity + 0.16 * size_extrapolation + 0.08 * unusual


def quantum_descriptors(fragments):
    profile=score_molecule(fragments); hetero=profile['hba']+profile['hbd']; aromatic=sum(f in ('benzene','pyridine','imidazole') for f in fragments); homo=-6.5+.18*hetero+.12*aromatic; lumo=-1.2-.15*hetero-.08*aromatic; gap=lumo-homo; hardness=gap/2; electrophilicity=((homo+lumo)/2)**2/max(2*hardness,1e-9); u=_applicability_uncertainty(fragments)
    values={"homo_ev":homo,"lumo_ev":lumo,"gap_ev":gap,"hardness_ev":hardness,"electrophilicity_ev":electrophilicity,"polar_surface_proxy":12.5*hetero,"partial_charge_span":min(2,.15*hetero)}
    return {**values,"uncertainty":{k: u*(1+abs(v)*.05) for k,v in values.items()},"applicability_uncertainty":u}

def admet_profile(fragments):
    m=score_molecule(fragments); permeability=1/(1+math.exp(-(m['logP']-1))) * 1/(1+m['hbd']/3); pgp=min(1,.08*m['hba']+.05*m['rotatable']); stability=max(0,1-m['cyp_risk']*.7-.03*m['rotatable']); hepatotoxicity=min(1,.35*m['cyp_risk']+.25*m['herg_risk']+.02*max(0,m['mw']-300)); u=_applicability_uncertainty(fragments)
    endpoint_scale={"logP":1.2,"logS":1.8,"permeability":.8,"cyp_risk":.9,"herg_risk":.9,"pgp_interaction":1.0,"metabolic_stability":1.1,"hepatotoxicity":1.2,"potency_prior":1.3,"synthetic_accessibility":1.0}
    uncertainty={key:u*scale for key,scale in endpoint_scale.items()}
    return {**m,"permeability":permeability,"pgp_interaction":pgp,"metabolic_stability":stability,"hepatotoxicity":hepatotoxicity,"uncertainty":uncertainty,"applicability_uncertainty":u,"model_status":"fragment/physics surrogate"}

def docking_score(fragments,pocket):
    profile=score_molecule(fragments); hb=min(profile['hba'],int(pocket.get('donors',2)))+min(profile['hbd'],int(pocket.get('acceptors',2))); hydrophobic=min(profile['logP'],float(pocket.get('hydrophobicity',2))); clash=max(0,profile['mw']-float(pocket.get('volume',400))*.8)/100; flexibility=.15*profile['rotatable']; dg=-1.4*hb-.8*hydrophobic+clash+flexibility
    u=_applicability_uncertainty(fragments)+.04*profile['rotatable']+.08*clash
    values={"binding_energy_kcal_mol":dg,"hydrogen_bonds":hb,"hydrophobic_score":hydrophobic,"clash_penalty":clash,"flexibility_penalty":flexibility}
    return {**values,"uncertainty":{k:u*(1+abs(float(v))*.04) for k,v in values.items()},"applicability_uncertainty":u,"interaction_fingerprint":{"hbond":hb>0,"hydrophobic":hydrophobic>1,"steric_clash":clash>0},"limitation":"Static surrogate omits explicit solvent, induced fit, and entropy."}

def md_binding_stability(binding_energy,flexibility,nanoseconds=100):
    if nanoseconds<=0 or flexibility<0: raise ValueError("invalid MD values")
    retention=1/(1+math.exp((binding_energy+5)+.2*flexibility)); off_rate=math.exp(binding_energy/2)*(.01+.01*flexibility); residence=1/max(off_rate,1e-12); u=.08+.03*flexibility+.01*abs(binding_energy)
    return {"trajectory_ns":nanoseconds,"bound_fraction":retention,"off_rate_per_ns":off_rate,"expected_residence_ns":residence,"uncertainty":{"bound_fraction":u,"off_rate_per_ns":u*off_rate,"expected_residence_ns":u*residence},"method":"accelerated stability surrogate, not molecular dynamics"}

def pareto_rank(candidates,objectives=None):
    objectives=objectives or {'potency':1,'solubility':1,'safety':1,'feasibility':1}
    enriched=[]
    for c in candidates:
        vector={k:float(c['objectives'][k])*float(w) for k,w in objectives.items()}; enriched.append({**c,"weighted_objectives":vector})
    front=pareto_front([{**c,"objectives":c['weighted_objectives']} for c in enriched]); return sorted(front,key=lambda x:-sum(x['objectives'].values()))

def retrosynthesis_plan(fragments,reagent_inventory=None):
    inventory=set(reagent_inventory or []); steps=_retro(fragments); enriched=[]
    for step in steps:
        reaction=step['reaction']; conditions={"amide coupling":{"solvent_class":"polar aprotic","catalyst_class":"coupling reagent","temperature_band_c":[15,30]},"cross-coupling":{"solvent_class":"mixed organic","catalyst_class":"transition metal","temperature_band_c":[50,100]},"alkylation":{"solvent_class":"polar aprotic","catalyst_class":"base","temperature_band_c":[20,70]}}[reaction]; available=step['disconnection'].replace('remove ','') in inventory; yield_prior={"amide coupling":.78,"cross-coupling":.7,"alkylation":.75}[reaction]; base_cost={"amide coupling":85.,"cross-coupling":145.,"alkylation":55.}[reaction]; inventory_discount=.35 if available else 1.; estimated_cost=base_cost*inventory_discount/yield_prior; enriched.append({**step,"conditions":conditions,"expected_yield":yield_prior,"reagent_available":available,"estimated_cost_usd":estimated_cost,"cost_yield_objective":estimated_cost/yield_prior})
    overall=float(np.prod([s['expected_yield'] for s in enriched])) if enriched else 1.; total=sum(s['estimated_cost_usd'] for s in enriched); objective=sum(s['cost_yield_objective'] for s in enriched); return {"steps":enriched,"step_count":len(enriched),"overall_yield":overall,"inventory_coverage":sum(s['reagent_available'] for s in enriched)/max(1,len(enriched)),"estimated_route_cost_usd":total,"cost_yield_objective":objective,"optimization_objective":"minimize cost per expected successful route","status":"planning-level route; not an executable lab protocol"}

def uncertainty_ensemble(fragments,n=200,seed=0,pocket=None):
    if n<2: raise ValueError("n must be >=2")
    admet=admet_profile(fragments); quantum=quantum_descriptors(fragments); docking=docking_score(fragments,pocket or {}); binding=md_binding_stability(docking["binding_energy_kcal_mol"],admet["rotatable"]); rng=np.random.default_rng(seed); metrics={}
    groups=((admet,admet["uncertainty"]),(quantum,quantum["uncertainty"]),(docking,docking["uncertainty"]),(binding,binding["uncertainty"]))
    for values, uncertainties in groups:
        for key,std in uncertainties.items():
            draws=rng.normal(float(values[key]),max(float(std),1e-9),n); metrics[key]={"mean":float(draws.mean()),"std":float(draws.std()),"ci90":[float(np.quantile(draws,.05)),float(np.quantile(draws,.95))]}
    return {"samples":n,"seed":seed,"metrics":metrics,"applicability_uncertainty":admet["applicability_uncertainty"]}

def active_learning_update(prior_mean,prior_std,observations,observation_std=.1):
    if min(prior_std,observation_std)<=0 or not observations: raise ValueError("positive uncertainty and observations required")
    p=1/prior_std**2; q=len(observations)/observation_std**2; mean=(p*prior_mean+sum(observations)/observation_std**2)/(p+q); return {"mean":mean,"std":math.sqrt(1/(p+q)),"observations":len(observations)}

def generate_conditioned(n=20,target=None,pocket=None,seed=0):
    target=target or {"logP":2,"min_solubility":.2,"max_toxicity":.4}; generated=generate(n,target.get('logP',2),seed); candidates=[]
    for c in generated['pareto_front']:
        dock=docking_score(c['fragments'],pocket or {}); admet=admet_profile(c['fragments']); condition_penalty=abs(admet['logP']-target.get('logP',2)) + max(0,target.get('min_solubility',0)-max(0,1+admet['logS']/4))+max(0,admet['hepatotoxicity']-target.get('max_toxicity',1)); reinforcement=-dock['binding_energy_kcal_mol']-condition_penalty; candidates.append({**c,"admet":admet,"docking":dock,"condition_penalty":condition_penalty,"reinforcement_score":reinforcement})
    candidates.sort(key=lambda x:-x['reinforcement_score']); return {"target":target,"candidates":candidates,"generated":n,"model_status":"Fragment sampler with explicit physics-informed ranking; no trained diffusion or transformer model."}

def molecule_diagnostics(fragments,pocket=None):
    m=admet_profile(fragments); q=quantum_descriptors(fragments); d=docking_score(fragments,pocket or {}); conf=conformer_ensemble(fragments,10,0); md=md_binding_stability(d['binding_energy_kcal_mol'],m['rotatable']); route=retrosynthesis_plan(fragments)
    out={"fragment_count":float(len(fragments)),"unique_fragment_count":float(len(set(fragments))),"heavy_atoms":float(sum(FRAGMENTS[f][1] for f in fragments)),"mw":m['mw'],"logP":m['logP'],"logS":m['logS'],"hbd":float(m['hbd']),"hba":float(m['hba']),"rotatable":float(m['rotatable']),"lipinski_violations":float(m['lipinski_violations']),"cyp_risk":m['cyp_risk'],"herg_risk":m['herg_risk'],"synthetic_accessibility":m['synthetic_accessibility'],"potency_prior":m['potency_prior'],"permeability":m['permeability'],"pgp_interaction":m['pgp_interaction'],"metabolic_stability":m['metabolic_stability'],"hepatotoxicity":m['hepatotoxicity'],**{f"quantum.{k}":float(v) for k,v in q.items() if isinstance(v,(int,float))},"docking_energy":d['binding_energy_kcal_mol'],"docking_hbonds":float(d['hydrogen_bonds']),"docking_clash":d['clash_penalty'],"docking_flexibility":d['flexibility_penalty'],"conformer_energy_min":conf[0]['energy_kcal_mol'],"conformer_energy_mean":float(np.mean([x['energy_kcal_mol'] for x in conf])),"conformer_rg_mean":float(np.mean([x['radius_gyration'] for x in conf])),"md_bound_fraction":md['bound_fraction'],"md_residence_ns":md['expected_residence_ns'],"route_steps":float(route['step_count']),"route_overall_yield":route['overall_yield'],"route_cost_usd":route['estimated_route_cost_usd'],"route_cost_yield_objective":route['cost_yield_objective']}
    return out

def discovery_package(fragments,pocket=None,background_inventory=None):
    profile=admet_profile(fragments); dock=docking_score(fragments,pocket or {}); return {"fragments":fragments,"graph":molecular_graph(fragments),"conformers":conformer_ensemble(fragments),"quantum":quantum_descriptors(fragments),"admet":profile,"docking":dock,"binding_stability":md_binding_stability(dock['binding_energy_kcal_mol'],profile['rotatable']),"retrosynthesis":retrosynthesis_plan(fragments,background_inventory),"uncertainty":uncertainty_ensemble(fragments),"diagnostics":molecule_diagnostics(fragments,pocket),"model_status":"Transparent fragment/physics surrogates; no trained model and not clinically validated.","next_steps":["Confirm identity and properties with independent cheminformatics or experimental measurements.","Assess target binding with explicit-solvent and induced-fit methods.","Review route feasibility, safety and reagent constraints with qualified chemists."]}
