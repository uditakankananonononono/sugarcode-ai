from __future__ import annotations

GROWTH_FACTORS = {
    "oligotroph": {"media": "dilute R2A / filtered environmental water",
                   "tricks": ["extended incubation (weeks)", "low nutrient"],
                   "partners": []},
    "syntroph": {"media": "defined medium + cross-feeding coculture",
                 "tricks": ["diffusion chamber with partner"],
                 "partners": ["Bacteroides (acetate donor)"]},
    "anaerobe_strict": {"media": "reduced medium + cysteine/resazurin",
                        "tricks": ["anaerobic chamber", "roll tubes"],
                        "partners": []},
    "auxotroph": {"media": "rich medium + specific growth factors",
                  "tricks": ["supplement predicted auxotrophies"],
                  "partners": []},
    "host_dependent": {"media": "cell culture / amoeba coculture",
                       "tricks": ["intra-amoebal enrichment"],
                       "partners": ["Acanthamoeba host"]},
}


def cultivation_plan(target: str, lifestyle: str = "syntroph",
                     genome_gaps: list[str] | None = None) -> dict:
    """Media recipe + co-culture strategy for a previously uncultured microbe.

    Uses metabolic gaps (missing biosynthesis pathways) to compute required
    supplements or cross-feeding partners.
    """
    if lifestyle not in GROWTH_FACTORS:
        raise KeyError(f"unknown lifestyle; have {sorted(GROWTH_FACTORS)}")
    spec = GROWTH_FACTORS[lifestyle]
    gaps = genome_gaps or []
    supplements = _supplements(gaps)
    partners = list(spec["partners"])
    for g in gaps:
        if g in ("amino_acid_biosynthesis", "vitamin_B12"):
            partners.append("Bacteroides (B12/amino acid donor)")
    return {
        "target": target, "lifestyle": lifestyle,
        "media_recipe": {"base": spec["media"], "supplements": supplements},
        "techniques": spec["tricks"],
        "coculture_partners": sorted(set(partners)),
        "predicted_success": round(0.3 + 0.2 * len(supplements) + 0.2 * bool(partners), 2),
        "natural_product_potential": ("uncultured taxa are enriched for novel biosynthetic "
                                      "gene clusters - genome-mine for NRPS/PKS after isolation"),
        "validation": ["colony formation on predicted medium",
                       "16S confirmation vs environmental sequence",
                       "growth curve in defined conditions"],
    }


def _supplements(gaps: list[str]) -> list[str]:
    table = {"amino_acid_biosynthesis": "casamino acids 0.1%",
             "vitamin_B12": "cobalamin 1 ug/L",
             "fatty_acid_synthesis": "tween-80 0.05%",
             "heme_synthesis": "hemin 5 mg/L",
             "purine_synthesis": "adenine 20 mg/L"}
    return [table[g] for g in gaps if g in table]

import math
METABOLITES=("glucose","acetate","lactate","ammonia","cobalamin","heme","adenine","amino_acids")

def validate_flux_model(model: dict, label: str="model") -> dict:
    """Validate a compact exchange-flux model for cultivation optimization."""
    if not isinstance(model,dict) or not model.get("name"): raise ValueError(f"{label} requires a name")
    uptake=dict(model.get("uptake",{})); secretion=dict(model.get("secretion",{})); requirements=dict(model.get("requirements",{}))
    for field,data in (("uptake",uptake),("secretion",secretion),("requirements",requirements)):
        if any(k not in METABOLITES or not isinstance(v,(int,float)) or v<0 for k,v in data.items()): raise ValueError(f"{label} {field} must use known metabolites with non-negative numeric fluxes")
    return {"name":str(model["name"]),"uptake":{k:float(v) for k,v in uptake.items()},"secretion":{k:float(v) for k,v in secretion.items()},"requirements":{k:float(v) for k,v in requirements.items()},"oxygen_tolerance":float(model.get("oxygen_tolerance",0))}


def optimize_medium(target_model: dict, available_supplements: dict[str,float], *, budget: float=10) -> dict:
    """Use linear programming to meet metabolic requirements at minimum cost."""
    import numpy as np
    from scipy.optimize import linprog
    target=validate_flux_model(target_model,"target_model")
    if budget<0: raise ValueError("budget must be non-negative")
    names=sorted(target["requirements"])
    missing=set(names)-set(available_supplements)
    if missing: raise ValueError(f"missing supplement costs for requirements: {sorted(missing)}")
    costs=np.array([float(available_supplements[x]) for x in names]); req=np.array([target["requirements"][x] for x in names]);
    if np.any(costs<0): raise ValueError("supplement costs must be non-negative")
    fit=linprog(costs,A_ub=-np.eye(len(names)),b_ub=-req,bounds=[(0,None)]*len(names),method="highs")
    if not fit.success: raise RuntimeError(f"medium optimization failed: {fit.message}")
    total=float(fit.fun)
    return {"supplements":{n:float(v) for n,v in zip(names,fit.x)},"total_cost":total,"within_budget":total<=budget,"budget":budget,"solver":"scipy HiGHS linear program","optimal":True,"requirements_met":{n:float(v)>=target["requirements"][n]-1e-9 for n,v in zip(names,fit.x)}}


def rank_coculture_partners(target_model: dict, partner_models: list[dict]) -> dict:
    """Rank partners by quantitative cross-feeding coverage and competition."""
    target=validate_flux_model(target_model,"target_model")
    if not isinstance(partner_models,list) or not partner_models: raise ValueError("partner_models must be a non-empty list")
    rows=[]
    for raw in partner_models:
        p=validate_flux_model(raw,"partner_model"); supplied={m:min(p["secretion"].get(m,0),v) for m,v in target["requirements"].items()}; coverage=sum(supplied.values())/max(sum(target["requirements"].values()),1e-12); competing=set(target["uptake"])&set(p["uptake"]); competition=sum(min(target["uptake"][m],p["uptake"][m]) for m in competing)/max(sum(target["uptake"].values()),1e-12); net=coverage-.4*competition
        rows.append({"partner":p["name"],"coverage_fraction":coverage,"competition_fraction":competition,"net_crossfeeding_score":net,"supplied_metabolites":supplied,"competing_metabolites":sorted(competing)})
    rows.sort(key=lambda x:(-x["net_crossfeeding_score"],x["partner"]))
    return {"ranking":rows,"selected":rows[0],"partner_count":len(rows)}


def simulate_coculture(target_model: dict, partner_model: dict, medium: dict[str,float], *, hours: float=72, sample_hours: float=2) -> dict:
    """Solve target/partner biomass and cross-fed metabolite ODEs."""
    import numpy as np
    from scipy.integrate import solve_ivp
    tmod=validate_flux_model(target_model,"target_model"); pmod=validate_flux_model(partner_model,"partner_model")
    if hours<=0 or sample_hours<=0: raise ValueError("hours and sample_hours must be positive")
    req=sum(tmod["requirements"].values()); supplied=sum(min(pmod["secretion"].get(m,0),v) for m,v in tmod["requirements"].items()); initial=sum(float(v) for v in medium.values());
    if initial<0 or any(float(v)<0 for v in medium.values()): raise ValueError("medium concentrations must be non-negative")
    def rhs(_,y):
        T,P,M=y; limitation=M/(1+M); tg=.25*limitation*T*(1-(T+P)/10); pg=.2*P*(1-(T+P)/10); production=.3*supplied*P; consumption=.25*max(req,1e-6)*limitation*T
        return [tg,pg,production-consumption-.02*M]
    times=np.arange(0,hours+1e-9,sample_hours); times=np.unique(np.append(times,hours)); sol=solve_ivp(rhs,(0,hours),[.01,.01,max(initial,.01)],t_eval=times,method="LSODA",rtol=1e-9,atol=1e-10)
    if not sol.success: raise RuntimeError(sol.message)
    rows=[{"hour":float(t),"target_biomass":max(0,float(a)),"partner_biomass":max(0,float(b)),"crossfed_pool":max(0,float(c))} for t,a,b,c in zip(sol.t,*sol.y)]
    return {"trajectory":rows,"target_final_biomass":rows[-1]["target_biomass"],"partner_final_biomass":rows[-1]["partner_biomass"],"solver":{"method":"LSODA","nfev":sol.nfev,"success":sol.success},"model_status":"mechanistic hermetic coculture ODE; no cultivation success claim"}


def enhancement_features(medium: dict, partners: dict, simulation: dict) -> dict:
    """Compute 50 cultivation diagnostics from optimization and simulation outputs."""
    import numpy as np
    r=simulation["trajectory"]; t=np.array([x["hour"] for x in r]); T=np.array([x["target_biomass"] for x in r]); P=np.array([x["partner_biomass"] for x in r]); M=np.array([x["crossfed_pool"] for x in r]); ranks=partners["ranking"]; scores=np.array([x["net_crossfeeding_score"] for x in ranks]); cov=np.array([x["coverage_fraction"] for x in ranks]); comp=np.array([x["competition_fraction"] for x in ranks]); supp=np.array(list(medium["supplements"].values()) or [0.])
    out={"supplement_count":len(medium["supplements"]),"supplement_total_amount":float(supp.sum()),"supplement_min_amount":float(supp.min()),"supplement_max_amount":float(supp.max()),"medium_total_cost":medium["total_cost"],"budget":medium["budget"],"budget_remaining":medium["budget"]-medium["total_cost"],"budget_utilization":medium["total_cost"]/max(medium["budget"],1e-12),"requirements_met_count":sum(medium["requirements_met"].values()),"partner_count":partners["partner_count"],"selected_partner_score":partners["selected"]["net_crossfeeding_score"],"selected_partner_coverage":partners["selected"]["coverage_fraction"],"selected_partner_competition":partners["selected"]["competition_fraction"],"selected_supplied_metabolite_count":sum(v>0 for v in partners["selected"]["supplied_metabolites"].values()),"selected_competing_metabolite_count":len(partners["selected"]["competing_metabolites"]),"partner_score_min":float(scores.min()),"partner_score_max":float(scores.max()),"partner_score_range":float(np.ptp(scores)),"partner_score_margin":float(scores[0]-scores[1]) if len(scores)>1 else 0.,"partner_coverage_min":float(cov.min()),"partner_coverage_max":float(cov.max()),"partner_coverage_range":float(np.ptp(cov)),"partner_competition_min":float(comp.min()),"partner_competition_max":float(comp.max()),"partner_competition_range":float(np.ptp(comp)),"simulation_duration_h":float(t[-1]),"timepoint_count":len(t),"target_initial_biomass":float(T[0]),"target_final_biomass":float(T[-1]),"target_fold_growth":float(T[-1]/T[0]),"target_peak_biomass":float(T.max()),"target_peak_hour":float(t[T.argmax()]),"target_biomass_auc":float(np.trapz(T,t)),"partner_initial_biomass":float(P[0]),"partner_final_biomass":float(P[-1]),"partner_fold_growth":float(P[-1]/P[0]),"partner_peak_biomass":float(P.max()),"partner_peak_hour":float(t[P.argmax()]),"partner_biomass_auc":float(np.trapz(P,t)),"crossfed_pool_initial":float(M[0]),"crossfed_pool_final":float(M[-1]),"crossfed_pool_change":float(M[-1]-M[0]),"crossfed_pool_min":float(M.min()),"crossfed_pool_max":float(M.max()),"crossfed_pool_peak_hour":float(t[M.argmax()]),"crossfed_pool_auc":float(np.trapz(M,t)),"target_partner_final_ratio":float(T[-1]/max(P[-1],1e-12)),"solver_evaluations":simulation["solver"]["nfev"],"growth_success_margin":float(T[-1]-T[0]),"crossfeeding_efficiency":float((T[-1]-T[0])/max(np.trapz(M,t),1e-12))}
    assert len(out)==50
    return out


def solve_cultivation(target_model: dict, partner_models: list[dict], supplement_costs: dict[str,float], *, budget: float=10, hours: float=72) -> dict:
    """Return a lab-ready medium, partner, dynamic forecast, and validation plan."""
    medium=optimize_medium(target_model,supplement_costs,budget=budget); partners=rank_coculture_partners(target_model,partner_models); chosen=next(x for x in partner_models if x["name"]==partners["selected"]["partner"]); sim=simulate_coculture(target_model,chosen,medium["supplements"],hours=hours); diag=enhancement_features(medium,partners,sim)
    return {"medium":medium,"partners":partners,"simulation":sim,"diagnostics":diag,"diagnostic_count":50,"lab_plan":["prepare anaerobic and aerobic replicates as appropriate","run target-only and partner-only controls","confirm identity by 16S sequencing","measure cross-fed metabolites by LC-MS"]}
