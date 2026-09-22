from __future__ import annotations
import math
from ..crispr_cargo.core import VEHICLES, pk_model

PROMOTERS = {
    "liver": ["TBG", "LP1"], "muscle": ["CK8", "MCK"], "cns": ["Syn1", "hGFAP"],
    "retina": ["RPE65", "CAG"], "heart": ["cTnT"], "ubiquitous": ["CAG", "EF1a"],
}


def optimize_gene_therapy(tissue: str, transgene_kb: float,
                          route: str = "iv") -> dict:
    """Vector + promoter + route optimization for a gene-therapy program."""
    prom = PROMOTERS.get(tissue.lower(), PROMOTERS["ubiquitous"])
    cands = []
    for name, v in VEHICLES.items():
        if not name.startswith("AAV"):
            continue
        trop = v["tissues"].get(tissue.lower(), 0.05)
        fit = 1.0 if transgene_kb <= v["cargo_kb"] else 0.0
        score = 0.6 * trop + 0.4 * fit
        cands.append({"vector": name, "score": round(score, 3), "tropism": trop,
                      "fits_transgene": bool(fit)})
    cands.sort(key=lambda c: -c["score"])
    best = cands[0] if cands and cands[0]["fits_transgene"] else None
    immune = _immune_model(best["vector"] if best else "AAV8", route)
    pk = pk_model(best["vector"], dose_ug=1e13 / 1e9, hours=24 * 7) if best else None
    return {
        "tissue": tissue, "transgene_kb": transgene_kb,
        "promoter_options": prom, "promoter_recommended": prom[0],
        "vector_ranking": cands, "selected": best,
        "delivery_route": route,
        "immune_response": immune,
        "pk": pk,
        "visualization": {"type": "route_map",
                          "stages": ["injection", "circulation", "tissue uptake",
                                     "endosomal escape", "nuclear entry", "expression"]},
        "efficiency_estimate": round(0.3 + 0.5 * (best["tropism"] if best else 0), 2),
    }


def _immune_model(vector: str, route: str) -> dict:
    preexisting = {"AAV2": 0.5, "AAV8": 0.25, "AAV9": 0.3}.get(vector, 0.3)
    route_risk = {"iv": 0.3, "intrathecal": 0.15, "subretinal": 0.05,
                  "intramuscular": 0.25}.get(route, 0.25)
    return {
        "preexisting_nab_prevalence": preexisting,
        "route_immunogenicity": route_risk,
        "mitigation": ["screen for neutralizing antibodies",
                       "transient immunosuppression (steroids/rituximab)",
                       "capsid engineering to escape NAbs (see Vector Opt)"],
        "combined_risk": round(1 - (1 - preexisting) * (1 - route_risk), 3),
    }

ROUTE_TISSUE_ACCESS={"iv":{"liver":1,"heart":.7,"muscle":.55,"cns":.08,"retina":.03},"intrathecal":{"cns":1,"retina":.1,"liver":.05},"subretinal":{"retina":1},"intramuscular":{"muscle":1,"heart":.2,"liver":.05}}

def validate_program(tissue: str, transgene_kb: float, route: str, dose_vg_per_kg: float) -> dict:
    """Validate a gene-therapy program against supported tissues, routes, and physical ranges."""
    t=tissue.lower()
    if t not in PROMOTERS: raise ValueError(f"unsupported tissue {tissue!r}; choose one of {sorted(PROMOTERS)}")
    if not isinstance(transgene_kb,(int,float)) or not 0<transgene_kb<=20: raise ValueError("transgene_kb must be > 0 and <= 20")
    if route not in ROUTE_TISSUE_ACCESS: raise ValueError(f"unsupported route {route!r}; choose one of {sorted(ROUTE_TISSUE_ACCESS)}")
    if not isinstance(dose_vg_per_kg,(int,float)) or not 1e8<=dose_vg_per_kg<=1e15: raise ValueError("dose_vg_per_kg must be between 1e8 and 1e15")
    access=ROUTE_TISSUE_ACCESS[route].get(t,.01)
    return {"tissue":t,"route":route,"route_access":access,"transgene_kb":float(transgene_kb),"dose_vg_per_kg":float(dose_vg_per_kg)}


def rank_vector_promoter_pairs(tissue: str, transgene_kb: float, route: str="iv",
                               *, nab_titer: float=0, dose_vg_per_kg: float=1e13) -> dict:
    """Rank executable AAV capsid-promoter programs under cargo, route, and immunity constraints."""
    if not 0<=nab_titer<=1: raise ValueError("nab_titer must be in [0, 1]")
    valid=validate_program(tissue,transgene_kb,route,dose_vg_per_kg); rows=[]
    promoter_strength={"TBG":.95,"LP1":.85,"CK8":.9,"MCK":.82,"Syn1":.9,"hGFAP":.75,"RPE65":.92,"CAG":.8,"cTnT":.9,"EF1a":.7}
    specificity={"TBG":.95,"LP1":.9,"CK8":.9,"MCK":.88,"Syn1":.92,"hGFAP":.9,"RPE65":.96,"CAG":.35,"cTnT":.93,"EF1a":.4}
    for vector,v in VEHICLES.items():
        if not vector.startswith("AAV"): continue
        cargo_margin=v["cargo_kb"]-transgene_kb; cargo_fit=max(0,min(1,1+cargo_margin/2))
        trop=v["tissues"].get(valid["tissue"],.02); immune=_immune_model(vector,route); immune_penalty=min(1,immune["combined_risk"]+.6*nab_titer)
        for promoter in PROMOTERS[valid["tissue"]]:
            expression=trop*valid["route_access"]*promoter_strength[promoter]*cargo_fit*(1-immune_penalty)
            score=.55*expression+.2*specificity[promoter]+.15*cargo_fit+.1*(1-immune_penalty)
            rows.append({"vector":vector,"promoter":promoter,"score":round(score,8),"predicted_expression":round(expression,8),"tropism":trop,
              "route_access":valid["route_access"],"cargo_margin_kb":round(cargo_margin,4),"fits_transgene":cargo_margin>=0,"immune_risk":round(immune_penalty,6),"promoter_specificity":specificity[promoter]})
    rows.sort(key=lambda x:(-x["score"],x["vector"],x["promoter"]))
    return {"program":valid,"nab_titer":nab_titer,"ranking":rows,"selected":next((x for x in rows if x["fits_transgene"]),None),
            "model_status":"mechanistic hermetic vector-promoter ranking; no delivery or efficacy claim"}


def simulate_delivery(tissue: str, vector: str, route: str, dose_vg_per_kg: float=1e13,
                      *, hours: float=168, sample_hours: float=6) -> dict:
    """Solve plasma, tissue, intracellular, and expression ODE compartments."""
    import numpy as np
    from scipy.integrate import solve_ivp
    validate_program(tissue,1,route,dose_vg_per_kg)
    if vector not in VEHICLES or not vector.startswith("AAV"): raise ValueError("vector must be a supported AAV capsid")
    if hours<=0 or sample_hours<=0: raise ValueError("hours and sample_hours must be positive")
    access=ROUTE_TISSUE_ACCESS[route].get(tissue.lower(),.01); trop=VEHICLES[vector]["tissues"].get(tissue.lower(),.02); ke=math.log(2)/VEHICLES[vector]["half_life_h"]
    def rhs(_,y):
        plasma,tissue_vg,intracellular,expression=y; uptake=.025*access*trop*plasma
        return [-ke*plasma-uptake,uptake-.015*tissue_vg,.015*tissue_vg-.008*intracellular,.004*intracellular-.02*expression]
    times=np.arange(0,hours+1e-9,sample_hours); times=np.unique(np.append(times,hours)); sol=solve_ivp(rhs,(0,hours),[dose_vg_per_kg,0,0,0],t_eval=times,method="LSODA",rtol=1e-8,atol=1e-6)
    if not sol.success: raise RuntimeError(sol.message)
    rows=[{"hour":round(float(t),5),"plasma_vg_per_kg":float(max(p,0)),"tissue_vg_per_kg":float(max(tv,0)),"intracellular_vg_per_kg":float(max(ic,0)),"expression_units":float(max(ex,0))} for t,p,tv,ic,ex in zip(sol.t,*sol.y)]
    expr=sol.y[3]
    return {"tissue":tissue.lower(),"vector":vector,"route":route,"dose_vg_per_kg":dose_vg_per_kg,"trajectory":rows,
      "peak_expression":float(expr.max()),"peak_expression_hour":float(sol.t[expr.argmax()]),"terminal_expression":float(expr[-1]),
      "solver":{"method":"LSODA","success":sol.success,"nfev":sol.nfev},"model_status":"mechanistic hermetic compartment ODE; no clinical dosing claim"}


def enhancement_features(ranking: dict, delivery: dict) -> dict:
    """Compute exactly 53 program-derived decision diagnostics."""
    import numpy as np
    rows=ranking["ranking"]; sel=ranking["selected"]; traj=delivery["trajectory"]
    score=np.asarray([x["score"] for x in rows]); exp=np.asarray([x["predicted_expression"] for x in rows]); immune=np.asarray([x["immune_risk"] for x in rows]); margins=np.asarray([x["cargo_margin_kb"] for x in rows])
    plasma=np.asarray([x["plasma_vg_per_kg"] for x in traj]); tissue=np.asarray([x["tissue_vg_per_kg"] for x in traj]); intracellular=np.asarray([x["intracellular_vg_per_kg"] for x in traj]); expression=np.asarray([x["expression_units"] for x in traj]); times=np.asarray([x["hour"] for x in traj])
    out={"candidate_pair_count":len(rows),"feasible_pair_count":sum(x["fits_transgene"] for x in rows),"infeasible_pair_count":sum(not x["fits_transgene"] for x in rows),"selected_score":sel["score"],"selected_expression":sel["predicted_expression"],
    "selected_tropism":sel["tropism"],"selected_route_access":sel["route_access"],"selected_cargo_margin_kb":sel["cargo_margin_kb"],"selected_immune_risk":sel["immune_risk"],"selected_promoter_specificity":sel["promoter_specificity"],
    "best_score_margin":float(score[0]-score[1]),"score_minimum":float(score.min()),"score_maximum":float(score.max()),"score_range":float(np.ptp(score)),"expression_minimum":float(exp.min()),"expression_maximum":float(exp.max()),
    "expression_range":float(np.ptp(exp)),"immune_risk_minimum":float(immune.min()),"immune_risk_maximum":float(immune.max()),"immune_risk_range":float(np.ptp(immune)),"cargo_margin_minimum_kb":float(margins.min()),
    "cargo_margin_maximum_kb":float(margins.max()),"capsid_count":len({x["vector"] for x in rows}),"promoter_count":len({x["promoter"] for x in rows}),"pairs_above_half_score":int(np.sum(score>.5)),"pairs_below_quarter_immune_risk":int(np.sum(immune<.25)),
    "simulation_timepoint_count":len(traj),"simulation_duration_hours":float(times[-1]),"dose_vg_per_kg":delivery["dose_vg_per_kg"],"initial_plasma_vg_per_kg":float(plasma[0]),"terminal_plasma_vg_per_kg":float(plasma[-1]),
    "plasma_fraction_remaining":float(plasma[-1]/max(plasma[0],1)),"peak_tissue_vg_per_kg":float(tissue.max()),"peak_tissue_hour":float(times[tissue.argmax()]),"terminal_tissue_vg_per_kg":float(tissue[-1]),"tissue_auc":float(np.trapz(tissue,times)),
    "peak_intracellular_vg_per_kg":float(intracellular.max()),"peak_intracellular_hour":float(times[intracellular.argmax()]),"terminal_intracellular_vg_per_kg":float(intracellular[-1]),"intracellular_auc":float(np.trapz(intracellular,times)),
    "peak_expression":float(expression.max()),"peak_expression_hour":float(times[expression.argmax()]),"terminal_expression":float(expression[-1]),"expression_auc":float(np.trapz(expression,times)),"expression_fraction_at_terminal":float(expression[-1]/max(expression.max(),1e-30)),
    "tissue_to_plasma_terminal_ratio":float(tissue[-1]/max(plasma[-1],1e-30)),"intracellular_to_tissue_terminal_ratio":float(intracellular[-1]/max(tissue[-1],1e-30)),"expression_onset_hour":float(times[np.argmax(expression>expression.max()*.1)]),
    "expression_above_half_peak_hours":float(np.trapz((expression>=expression.max()*.5).astype(float),times)),"plasma_half_life_observed_hour":float(times[np.argmax(plasma<=plasma[0]/2)]) if np.any(plasma<=plasma[0]/2) else float(times[-1]),
    "mass_balance_terminal_fraction":float((plasma[-1]+tissue[-1]+intracellular[-1])/max(plasma[0],1)),"solver_evaluations":delivery["solver"]["nfev"],"program_delivery_alignment":float(sel["tropism"]*sel["route_access"]*(1-sel["immune_risk"]))}
    assert len(out)==53
    return out


def design_gene_therapy_program(tissue: str, transgene_kb: float, route: str="iv", *, nab_titer: float=0,
                                dose_vg_per_kg: float=1e13, hours: float=168) -> dict:
    """Return a lab-reviewable vector, promoter, immunity, and delivery program."""
    ranked=rank_vector_promoter_pairs(tissue,transgene_kb,route,nab_titer=nab_titer,dose_vg_per_kg=dose_vg_per_kg)
    if ranked["selected"] is None: raise ValueError("transgene does not fit any supported AAV; consider a split vector or non-AAV vehicle")
    sel=ranked["selected"]; delivery=simulate_delivery(tissue,sel["vector"],route,dose_vg_per_kg,hours=hours); diagnostics=enhancement_features(ranked,delivery)
    return {"ranking":ranked,"selected_program":sel,"delivery_simulation":delivery,"diagnostics":diagnostics,"diagnostic_count":53,
      "visualization":{"type":"3d_route_trace","coordinates":[[i,x["tissue_vg_per_kg"],x["expression_units"]] for i,x in enumerate(delivery["trajectory"])]},
      "lab_plan":["confirm cassette size including ITRs","screen neutralizing antibodies","validate tissue-specific expression in primary cells","establish biodistribution and shedding assays"],
      "model_status":"mechanistic hermetic program design; no clinical efficacy or dosing claim"}
