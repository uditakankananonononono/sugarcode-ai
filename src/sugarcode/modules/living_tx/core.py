from __future__ import annotations
import numpy as _np
_trapz = getattr(_np, "trapezoid", None) or _np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0

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

import math

def validate_design_inputs(payload: str, chassis: str, dose_cfu: float) -> dict:
    """Validate a living-therapeutic design against supported payload and chassis data."""
    if payload not in PAYLOADS: raise ValueError(f"payload must be one of {sorted(PAYLOADS)}")
    if chassis not in CHASSIS: raise ValueError(f"chassis must be one of {sorted(CHASSIS)}")
    if not isinstance(dose_cfu,(int,float)) or not 1e5<=dose_cfu<=1e12: raise ValueError("dose_cfu must be between 1e5 and 1e12")
    return {"payload":payload,"chassis":chassis,"dose_cfu":float(dose_cfu)}


def rank_designs(payload: str, *, dose_cfu: float=1e9) -> dict:
    """Rank chassis choices by safety, engineering, engraftment, and disruption."""
    if payload not in PAYLOADS: raise ValueError(f"payload must be one of {sorted(PAYLOADS)}")
    rows=[]
    for chassis,c in CHASSIS.items():
        validate_design_inputs(payload,chassis,dose_cfu); impact=_community_sim(chassis,payload); payload_risk=PAYLOADS[payload]["risk"]; containment_need=.5*payload_risk+.3*(1-c["safety"])+.2*c["engraftment"]
        # Payload and dose interact non-uniformly with chassis traits. High-risk
        # cytokines strongly reward safety; low dose rewards engraftment, while
        # high dose rewards engineering/control and penalizes disruption.
        dose_scale=max(0.,min(1.,(math.log10(dose_cfu)-5)/7))
        low_dose=1-dose_scale
        safety_weight=.18+.42*payload_risk
        engraft_weight=.12+.38*low_dose
        engineering_weight=.12+.3*dose_scale
        disruption_weight=.12+.18*dose_scale
        payload_fit={
          "IL-22":{"E_coli_Nissle":.85,"Lactobacillus":1.,"Bacteroides":.7,"S_boulardii":.75},
          "IL-10":{"E_coli_Nissle":.9,"Lactobacillus":1.,"Bacteroides":.8,"S_boulardii":.7},
          "GLP-1":{"E_coli_Nissle":1.,"Lactobacillus":.65,"Bacteroides":.75,"S_boulardii":.9},
          "phenylalanine_degradase":{"E_coli_Nissle":1.,"Lactobacillus":.55,"Bacteroides":.9,"S_boulardii":.6},
          "oxalate_decarboxylase":{"E_coli_Nissle":.7,"Lactobacillus":.9,"Bacteroides":1.,"S_boulardii":.55},
        }[payload][chassis]
        norm=safety_weight+engraft_weight+engineering_weight+disruption_weight+.22
        score=(safety_weight*c["safety"]+engraft_weight*c["engraftment"]+engineering_weight*c["engineering_ease"]+disruption_weight*(1-impact["disruption_index"])+.22*payload_fit)/norm
        rows.append({"chassis":chassis,"score":round(score,8),"safety":c["safety"],"engineering_ease":c["engineering_ease"],"engraftment":c["engraftment"],"disruption_index":impact["disruption_index"],"containment_need":containment_need,"payload_fit":payload_fit,"dose_scale":dose_scale})
    rows.sort(key=lambda x:(-x["score"],x["chassis"]))
    return {"payload":payload,"dose_cfu":dose_cfu,"ranking":rows,"selected":rows[0]}


def simulate_gut_community(chassis: str, payload: str, *, dose_cfu: float=1e9, days: float=56, sample_hours: float=12) -> dict:
    """Solve engineered strain, residents, substrate, and therapeutic ODEs."""
    import numpy as np
    _trapz = getattr(np, "trapezoid", None) or np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0
    from scipy.integrate import solve_ivp
    validate_design_inputs(payload,chassis,dose_cfu)
    if days<=0 or sample_hours<=0: raise ValueError("days and sample_hours must be positive")
    c=CHASSIS[chassis]; risk=PAYLOADS[payload]["risk"]
    # scaled biomass units, secretion driven by engineered population.
    def rhs(_,y):
        engineered,residents,substrate,compound=y; total=engineered+residents; ge=.5*c["engraftment"]*engineered*substrate*(1-total/10); gr=.35*residents*substrate*(1-total/10); use=.05*(engineered+residents)*substrate
        return [ge-.08*(1-c["engraftment"])*engineered,gr-.03*c["engraftment"]*engineered*residents,-use+.02*(1-substrate),.12*(1-risk)*engineered-.18*compound]
    times=np.arange(0,days*24+1e-9,sample_hours); times=np.unique(np.append(times,days*24)); initial_engineered=max(.001,min(2,dose_cfu/1e10)); sol=solve_ivp(rhs,(0,days*24),[initial_engineered,5,1,0],t_eval=times,method="LSODA",rtol=1e-9,atol=1e-10)
    if not sol.success: raise RuntimeError(sol.message)
    rows=[]
    for h,e,r,s,p in zip(sol.t,*sol.y):
        vals=[max(0,float(x)) for x in (e,r,s,p)]; rows.append({"hour":float(h),"engineered_biomass":vals[0],"resident_biomass":vals[1],"substrate":vals[2],"therapeutic_compound":vals[3],"engineered_fraction":vals[0]/max(vals[0]+vals[1],1e-12)})
    return {"chassis":chassis,"payload":payload,"dose_cfu":dose_cfu,"trajectory":rows,"terminal_engraftment_fraction":rows[-1]["engineered_fraction"],"terminal_compound":rows[-1]["therapeutic_compound"],"solver":{"method":"LSODA","nfev":sol.nfev,"success":sol.success},"model_status":"mechanistic hermetic gut-community ODE; no clinical success prediction"}


def containment_risk(chassis: str, payload: str, simulation: dict) -> dict:
    """Calculate release, persistence, payload, and horizontal-transfer risks."""
    c=CHASSIS[chassis]; p=PAYLOADS[payload]; persistence=simulation["terminal_engraftment_fraction"]; hgt=.02*c["engineering_ease"]*(1-c["safety"]+.05); shedding=min(1,.3+persistence); total=1-math.prod([1-p["risk"],1-persistence*.3,1-hgt,1-shedding*.1])
    return {"payload_risk":p["risk"],"persistence_risk":persistence*.3,"horizontal_transfer_risk":hgt,"shedding_risk":shedding*.1,"combined_risk":total,"required_controls":["dual independent kill switches","validated auxotrophy","environmental shedding assay","antibiotic-resistance-marker-free construct"]}


def enhancement_features(ranking: dict, simulation: dict, risk: dict) -> dict:
    """Compute 50 design/community/containment diagnostics."""
    import numpy as np
    rows=ranking["ranking"]; scores=np.array([x["score"] for x in rows]); disrupt=np.array([x["disruption_index"] for x in rows]); contain=np.array([x["containment_need"] for x in rows]); r=simulation["trajectory"]; t=np.array([x["hour"] for x in r]); E=np.array([x["engineered_biomass"] for x in r]); R=np.array([x["resident_biomass"] for x in r]); S=np.array([x["substrate"] for x in r]); C=np.array([x["therapeutic_compound"] for x in r]); F=np.array([x["engineered_fraction"] for x in r]); sel=ranking["selected"]
    out={"design_candidate_count":len(rows),"selected_score":sel["score"],"selected_safety":sel["safety"],"selected_engineering_ease":sel["engineering_ease"],"selected_engraftment":sel["engraftment"],"selected_disruption_index":sel["disruption_index"],"selected_containment_need":sel["containment_need"],"score_min":float(scores.min()),"score_max":float(scores.max()),"score_range":float(np.ptp(scores)),"score_margin":float(scores[0]-scores[1]),"disruption_min":float(disrupt.min()),"disruption_max":float(disrupt.max()),"disruption_range":float(np.ptp(disrupt)),"containment_need_min":float(contain.min()),"containment_need_max":float(contain.max()),"simulation_duration_h":float(t[-1]),"timepoint_count":len(t),"initial_engineered_biomass":float(E[0]),"final_engineered_biomass":float(E[-1]),"engineered_fold_change":float(E[-1]/E[0]),"peak_engineered_biomass":float(E.max()),"peak_engineered_hour":float(t[E.argmax()]),"engineered_auc":float(_trapz(E,t)),"initial_resident_biomass":float(R[0]),"final_resident_biomass":float(R[-1]),"resident_fold_change":float(R[-1]/R[0]),"minimum_resident_biomass":float(R.min()),"resident_auc":float(_trapz(R,t)),"initial_substrate":float(S[0]),"final_substrate":float(S[-1]),"minimum_substrate":float(S.min()),"substrate_auc":float(_trapz(S,t)),"final_compound":float(C[-1]),"peak_compound":float(C.max()),"peak_compound_hour":float(t[C.argmax()]),"compound_auc":float(_trapz(C,t)),"initial_engineered_fraction":float(F[0]),"final_engineered_fraction":float(F[-1]),"peak_engineered_fraction":float(F.max()),"engraftment_fraction_change":float(F[-1]-F[0]),"payload_risk":risk["payload_risk"],"persistence_risk":risk["persistence_risk"],"horizontal_transfer_risk":risk["horizontal_transfer_risk"],"shedding_risk":risk["shedding_risk"],"combined_containment_risk":risk["combined_risk"],"risk_control_count":len(risk["required_controls"]),"solver_evaluations":simulation["solver"]["nfev"],"compound_per_engineered_auc":float(_trapz(C,t)/max(_trapz(E,t),1e-12)),"resident_displacement_fraction":float(1-R[-1]/R[0])}
    assert len(out)==50
    return out


def design_living_therapy(payload: str, *, dose_cfu: float=1e9, days: float=56) -> dict:
    """Engineered probiotic program with community and containment evidence.

    Ready only when the selected chassis persists in the community simulation;
    washout or resident takeover is reported as a failure, with any chassis that
    do persist at this dose."""
    ranking=rank_designs(payload,dose_cfu=dose_cfu); chassis=ranking["selected"]["chassis"]; sim=simulate_gut_community(chassis,payload,dose_cfu=dose_cfu,days=days); risk=containment_risk(chassis,payload,sim);     diag=enhancement_features(ranking,sim,risk)
    verdict=simulation_verdict(sim)
    if verdict["status"]!="persists":
        verdict["persisting_alternatives"]=[r["chassis"] for r in ranking["ranking"] if r["chassis"]!=chassis and simulation_verdict(simulate_gut_community(r["chassis"],payload,dose_cfu=dose_cfu,days=days,sample_hours=24))["status"]=="persists"]
    return {"ranking":ranking,"simulation":sim,"containment":risk,"diagnostics":diag,"diagnostic_count":50,"verdict":verdict,"readiness":"ready_for_lab" if verdict["status"]=="persists" else "not_ready","genetic_program":{"payload":payload,"expression":"environment-responsive inducible circuit","secretion":"validated export signal","containment":risk["required_controls"]},"development_plan":["verify construct sequence and stability","measure secretion kinetics","test community impact in defined consortia","run shedding and kill-switch escape assays"]}


WASHOUT_FRACTION = 1e-4   # final engineered fraction below this: washed out
TAKEOVER_FRACTION = 0.9   # final engineered fraction above this: residents displaced



def simulation_verdict(simulation: dict) -> dict:
    """Classify a community simulation from its terminal engineered fraction.

    washed_out: the engineered strain is effectively gone (below
    WASHOUT_FRACTION) - it cannot deliver payload at this dose.
    resident_takeover: it dominates (above TAKEOVER_FRACTION), displacing the
    resident community - a safety concern, not a success.
    persists: in between.
    """
    f=simulation["terminal_engraftment_fraction"]
    status="washed_out" if f<WASHOUT_FRACTION else "resident_takeover" if f>TAKEOVER_FRACTION else "persists"
    return {"status":status,"terminal_engraftment_fraction":f,"terminal_compound":simulation["terminal_compound"],"thresholds":{"washout_fraction":WASHOUT_FRACTION,"takeover_fraction":TAKEOVER_FRACTION},"basis":"final engineered fraction of community biomass at simulation end"}
