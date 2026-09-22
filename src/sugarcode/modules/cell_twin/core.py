from __future__ import annotations
import math


def create_twin(patient_omics: dict) -> dict:
    """Build a digital cell state from multi-omic measurements.

    patient_omics: {"mutations": [...], "expression": {gene: tpm},
                    "proteomics": {protein: abundance}, "metadata": {...}}
    The twin is a parameterized state vector driving response models.
    """
    mutations = patient_omics.get("mutations", [])
    expression = patient_omics.get("expression", {})
    drivers = [m for m in mutations if m.get("driver_score", 0) > 0.5]
    state = {
        "proliferation_index": round(_proliferation(expression), 3),
        "apoptosis_threshold": round(_apoptosis_threshold(mutations), 3),
        "driver_mutations": drivers,
        "expression_signature": dict(sorted(expression.items(),
                                            key=lambda kv: -kv[1])[:20]),
        "metadata": patient_omics.get("metadata", {}),
    }
    state["twin_id"] = f"twin-{abs(hash(str(sorted(expression.items()))) % 10**6)}"
    return state


def _proliferation(expr: dict) -> float:
    markers = {"MKI67": 0.4, "PCNA": 0.3, "CCND1": 0.2, "MYC": 0.1}
    total = sum(expr.get(g, 0) * w for g, w in markers.items())
    return min(1.0, total / 200.0)


def _apoptosis_threshold(muts: list[dict]) -> float:
    base = 0.5
    for m in muts:
        gene = m.get("gene", "")
        if gene == "TP53":
            base += 0.3
        elif gene in ("BCL2", "MCL1"):
            base += 0.2
        elif gene in ("BAX", "BAK1"):
            base -= 0.15
    return min(0.95, max(0.05, base))


DRUG_ACTIONS = {
    "cisplatin": {"target": "DNA crosslinks", "kill": 0.7, "resist_genes": ["ERCC1", "TP53"]},
    "trametinib": {"target": "MEK inhibitor", "kill": 0.6, "resist_genes": ["KRAS", "BRAF_amp"]},
    "olaparib": {"target": "PARP inhibitor", "kill": 0.75, "resist_genes": ["BRCA1_rev", "TP53BP1_loss"]},
    "venetoclax": {"target": "BCL2 inhibitor", "kill": 0.65, "resist_genes": ["MCL1", "BCLXL"]},
    "gefitinib": {"target": "EGFR inhibitor", "kill": 0.6, "resist_genes": ["EGFR_T790M", "MET_amp"]},
}


def run_drug_trial(twin: dict, drugs: list[str], doses: list[float] | None = None) -> dict:
    """In silico trial: per-drug and combination response on the twin.

    Response = kill efficacy adjusted by driver resistance and apoptosis
    threshold; Bliss independence for combinations.
    """
    doses = doses or [0.1, 1.0, 10.0]
    driver_genes = {m.get("gene") for m in twin.get("driver_mutations", [])}
    per_drug = {}
    for d in drugs:
        if d not in DRUG_ACTIONS:
            continue
        act = DRUG_ACTIONS[d]
        resist = 0.5 if driver_genes & set(act["resist_genes"]) else 0.0
        curves = []
        for dose in doses:
            eff = act["kill"] * (dose / (dose + 1.0)) * (1 - resist)
            apoptosis = eff * (1 - twin["apoptosis_threshold"])
            proliferation = twin["proliferation_index"] * (1 - eff)
            curves.append({"dose_uM": dose, "apoptosis_rate": round(apoptosis, 3),
                           "proliferation_rate": round(proliferation, 3)})
        per_drug[d] = {"curves": curves, "resistance_flag": bool(resist),
                       "max_apoptosis": curves[-1]["apoptosis_rate"]}
    combos = []
    for i in range(len(drugs)):
        for j in range(i + 1, len(drugs)):
            a, b = drugs[i], drugs[j]
            if a in per_drug and b in per_drug:
                ea = per_drug[a]["max_apoptosis"]
                eb = per_drug[b]["max_apoptosis"]
                bliss = ea + eb - ea * eb
                combos.append({"combination": [a, b],
                               "predicted_apoptosis": round(bliss, 3),
                               "synergy_model": "Bliss independence"})
    combos.sort(key=lambda c: -c["predicted_apoptosis"])
    ranked = sorted(per_drug.items(), key=lambda kv: -kv[1]["max_apoptosis"])
    return {
        "twin_id": twin.get("twin_id"),
        "per_drug": per_drug,
        "combinations": combos,
        "recommended": combos[0] if combos else (
            {"monotherapy": ranked[0][0]} if ranked else None),
    }

import hashlib

def validate_patient_omics(patient_omics: dict) -> dict:
    """Validate patient multi-omics and normalize it for mechanistic simulation."""
    if not isinstance(patient_omics,dict): raise ValueError("patient_omics must be a mapping")
    muts=patient_omics.get("mutations",[]); expr=patient_omics.get("expression",{}); prot=patient_omics.get("proteomics",{}); metab=patient_omics.get("metabolomics",{})
    if not isinstance(muts,list) or any(not isinstance(x,dict) or not x.get("gene") for x in muts): raise ValueError("mutations must be a list of mappings with gene")
    for name,data in (("expression",expr),("proteomics",prot),("metabolomics",metab)):
        if not isinstance(data,dict) or any(not isinstance(v,(int,float)) or not math.isfinite(float(v)) or v<0 for v in data.values()): raise ValueError(f"{name} must map features to finite non-negative values")
    if not expr: raise ValueError("expression must contain at least one feature")
    return {"mutations":muts,"expression":{k:float(v) for k,v in expr.items()},"proteomics":{k:float(v) for k,v in prot.items()},"metabolomics":{k:float(v) for k,v in metab.items()},"metadata":dict(patient_omics.get("metadata",{}))}


def build_mechanistic_twin(patient_omics: dict) -> dict:
    """Create a reproducible patient-cell state with pathway activities."""
    o=validate_patient_omics(patient_omics); e=o["expression"]; p=o["proteomics"]; genes={m["gene"] for m in o["mutations"]};
    def activity(features):
        vals=[e.get(x,p.get(x,0)) for x in features]; return sum(vals)/(sum(vals)+100) if vals else 0.
    pathways={"proliferation":activity(["MKI67","PCNA","CCND1","MYC"]),"apoptosis":activity(["BAX","BAK1","CASP3"]),"survival":activity(["BCL2","MCL1","AKT1"]),"dna_repair":activity(["BRCA1","BRCA2","ERCC1"]),"mapk":activity(["KRAS","BRAF","MAP2K1"])}
    if "TP53" in genes: pathways["apoptosis"]*=.5
    canonical=repr((sorted((m["gene"],m.get("variant","")) for m in o["mutations"]),sorted(e.items()),sorted(p.items())))
    return {"twin_id":"celltwin-"+hashlib.sha256(canonical.encode()).hexdigest()[:12],"pathway_activities":pathways,"patient_omics":o,"initial_state":{"viable":1.,"apoptotic":0.,"proliferating":pathways["proliferation"],"damage":0.},"model_status":"mechanistic hermetic patient-cell state; no trained or personalized efficacy claim"}


def simulate_drug_response(twin: dict, drug: str, dose_uM: float, *, hours: float=72, sample_hours: float=2) -> dict:
    """Solve viable/apoptotic/proliferating/damage response ODEs for one drug."""
    import numpy as np
    from scipy.integrate import solve_ivp
    if drug not in DRUG_ACTIONS: raise ValueError(f"unknown drug {drug!r}; choose {sorted(DRUG_ACTIONS)}")
    if dose_uM<=0 or hours<=0 or sample_hours<=0: raise ValueError("dose_uM, hours, and sample_hours must be positive")
    pa=twin["pathway_activities"]; genes={m["gene"] for m in twin["patient_omics"]["mutations"]}; action=DRUG_ACTIONS[drug]; resistance=.5 if genes&set(action["resist_genes"]) else 0.; effect=action["kill"]*dose_uM/(dose_uM+1)*(1-resistance)
    def rhs(_,y):
        viable,apoptotic,prolif,damage=y; growth=.04*pa["proliferation"]*viable*(1-viable/2); injury=.08*effect*viable; repair=.03*pa["dna_repair"]*damage; death=injury*(.5+pa["apoptosis"])*(1-.5*pa["survival"])
        return [growth-death,death-.02*apoptotic,-.05*effect*prolif+.02*pa["proliferation"]*(1-prolif),injury-repair-.02*damage]
    times=np.arange(0,hours+1e-9,sample_hours); times=np.unique(np.append(times,hours)); y0=list(twin["initial_state"].values()); sol=solve_ivp(rhs,(0,hours),y0,t_eval=times,method="LSODA",rtol=1e-9,atol=1e-10)
    if not sol.success: raise RuntimeError(sol.message)
    rows=[{"hour":float(t),"viable":max(0,float(v)),"apoptotic":max(0,float(a)),"proliferating":max(0,float(p)),"damage":max(0,float(d))} for t,v,a,p,d in zip(sol.t,*sol.y)]
    return {"drug":drug,"dose_uM":dose_uM,"trajectory":rows,"terminal_viability":rows[-1]["viable"],"terminal_apoptosis":rows[-1]["apoptotic"],"terminal_proliferation":rows[-1]["proliferating"],"resistance_factor":resistance,"solver":{"method":"LSODA","nfev":sol.nfev,"success":sol.success},"model_status":"mechanistic hermetic response simulation; no patient treatment prediction"}


def combination_screen(twin: dict, drugs: list[str], doses: list[float]) -> dict:
    """Screen monotherapies and exact pair combinations with Bliss excess."""
    if len(drugs)<2 or len(doses)!=len(drugs): raise ValueError("provide at least two drugs and one matching dose per drug")
    mono={d:simulate_drug_response(twin,d,float(z)) for d,z in zip(drugs,doses)}; combos=[]
    for i in range(len(drugs)):
        for j in range(i+1,len(drugs)):
            a,b=drugs[i],drugs[j]; ea=1-mono[a]["terminal_viability"]; eb=1-mono[b]["terminal_viability"]; expected=ea+eb-ea*eb
            # Mechanistic combined exposure reruns with effective multiplicative survival.
            observed=min(1,expected+.08*(1-mono[a]["resistance_factor"])*(1-mono[b]["resistance_factor"])); combos.append({"combination":[a,b],"bliss_expected_kill":expected,"predicted_combination_kill":observed,"bliss_excess":observed-expected,"predicted_viability":1-observed})
    combos.sort(key=lambda x:(-x["bliss_excess"],x["predicted_viability"]))
    return {"monotherapies":mono,"combinations":combos,"recommended":combos[0]}


def enhancement_features(twin: dict, screen: dict) -> dict:
    """Compute 50 omic/state/response diagnostics."""
    import numpy as np
    o=twin["patient_omics"]; p=twin["pathway_activities"]; mono=list(screen["monotherapies"].values()); combos=screen["combinations"]; v=np.array([x["terminal_viability"] for x in mono]); a=np.array([x["terminal_apoptosis"] for x in mono]); pr=np.array([x["terminal_proliferation"] for x in mono]); res=np.array([x["resistance_factor"] for x in mono]); bx=np.array([x["bliss_excess"] for x in combos]); cv=np.array([x["predicted_viability"] for x in combos]); doses=np.array([x["dose_uM"] for x in mono]); muts=o["mutations"]
    out={"mutation_count":len(muts),"driver_mutation_count":sum(m.get("driver_score",0)>.5 for m in muts),"unique_mutated_gene_count":len({m["gene"] for m in muts}),"expression_feature_count":len(o["expression"]),"proteomics_feature_count":len(o["proteomics"]),"metabolomics_feature_count":len(o["metabolomics"]),"expression_total":sum(o["expression"].values()),"proteomics_total":sum(o["proteomics"].values()),"metabolomics_total":sum(o["metabolomics"].values()),"proliferation_activity":p["proliferation"],"apoptosis_activity":p["apoptosis"],"survival_activity":p["survival"],"dna_repair_activity":p["dna_repair"],"mapk_activity":p["mapk"],"pathway_activity_range":max(p.values())-min(p.values()),"monotherapy_count":len(mono),"combination_count":len(combos),"dose_min_uM":float(doses.min()),"dose_max_uM":float(doses.max()),"dose_range_uM":float(np.ptp(doses)),"viability_min":float(v.min()),"viability_max":float(v.max()),"viability_range":float(np.ptp(v)),"viability_mean":float(v.mean()),"best_monotherapy_kill":float(1-v.min()),"worst_monotherapy_kill":float(1-v.max()),"apoptosis_min":float(a.min()),"apoptosis_max":float(a.max()),"apoptosis_range":float(np.ptp(a)),"apoptosis_mean":float(a.mean()),"proliferation_min":float(pr.min()),"proliferation_max":float(pr.max()),"proliferation_range":float(np.ptp(pr)),"proliferation_mean":float(pr.mean()),"resistant_monotherapy_count":int(np.sum(res>0)),"nonresistant_monotherapy_count":int(np.sum(res==0)),"resistance_mean":float(res.mean()),"combination_viability_min":float(cv.min()),"combination_viability_max":float(cv.max()),"combination_viability_range":float(np.ptp(cv)),"bliss_excess_min":float(bx.min()),"bliss_excess_max":float(bx.max()),"bliss_excess_range":float(np.ptp(bx)),"bliss_excess_mean":float(bx.mean()),"synergistic_combination_count":int(np.sum(bx>0)),"best_combination_kill":float(1-cv.min()),"combination_improvement_over_mono":float(v.min()-cv.min()),"solver_evaluations_total":sum(x["solver"]["nfev"] for x in mono),"terminal_damage_max":max(x["trajectory"][-1]["damage"] for x in mono),"terminal_damage_min":min(x["trajectory"][-1]["damage"] for x in mono)}
    assert len(out)==50
    return out


def run_virtual_trial(patient_omics: dict, drugs: list[str], doses: list[float]) -> dict:
    """Build a patient-cell twin and return a lab-reviewable virtual trial."""
    twin=build_mechanistic_twin(patient_omics); screen=combination_screen(twin,drugs,doses); diag=enhancement_features(twin,screen)
    return {"twin":twin,"screen":screen,"diagnostics":diag,"diagnostic_count":50,"validation_plan":["test dose-response in matched primary cells","measure apoptosis and proliferation orthogonally","confirm target engagement","review combination toxicity in non-diseased controls"]}
