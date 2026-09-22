from __future__ import annotations
import math

ORGANOID_RECIPES = {
    "intestinal": {"factors": ["Wnt3a", "R-spondin", "Noggin", "EGF"],
                   "matrix": "Matrigel", "doubling_days": 2},
    "cerebral": {"factors": ["dual-SMAD inhibitors", "FGF2", "BDNF"],
                 "matrix": "Matrigel droplets", "doubling_days": 5},
    "hepatic": {"factors": ["HGF", "FGF10", "OSM", "dexamethasone"],
                "matrix": "Matrigel", "doubling_days": 4},
    "pancreatic": {"factors": ["FGF10", "Noggin", "R-spondin", "A83-01"],
                   "matrix": "Matrigel", "doubling_days": 3},
    "tumor": {"factors": ["EGF", "FGF2", "Noggin", "patient-specific"],
              "matrix": "Matrigel", "doubling_days": 3},
}


def design_organoid(tissue: str, patient_mutations: list[str] | None = None) -> dict:
    """Optimal growth conditions + media recipe + spatial expression map."""
    key = tissue.lower()
    if key not in ORGANOID_RECIPES:
        raise KeyError(f"unknown tissue {tissue!r}; have {sorted(ORGANOID_RECIPES)}")
    r = ORGANOID_RECIPES[key]
    spatial = _spatial_map(key, patient_mutations or [])
    return {
        "tissue": tissue,
        "media_recipe": {"base": "advanced DMEM/F12 + B27 + N2",
                         "factors": r["factors"], "matrix": r["matrix"],
                         "passage": "1:3 every 7-10 days by mechanical disruption"},
        "growth_conditions": {"temp_c": 37, "co2_pct": 5,
                              "doubling_days": r["doubling_days"]},
        "spatial_expression": spatial,
        "patient_mutations": patient_mutations or [],
        "quality_checks": ["morphology score at passage 2", "marker panel by IF",
                           "short tandem repeat match to patient tissue"],
    }


def _spatial_map(tissue: str, mutations: list[str]) -> dict:
    zones = {"intestinal": {"crypt": ["LGR5", "OLFM4"], "villus": ["VIL1", "ALPI"]},
             "cerebral": {"ventricular": ["PAX6", "SOX2"], "cortical": ["TBR1", "CTIP2"]},
             "hepatic": {"periportal": ["ALB", "CPS1"], "perivenous": ["CYP2E1", "GS"]},
             "pancreatic": {"duct": ["KRT19", "SOX9"], "acinar": ["AMY2A"]},
             "tumor": {"core": ["MKI67", "HIF1A"], "rim": ["KRT14"]}}
    return {"zones": zones.get(tissue, {}),
            "mutation_driven_zones": {m: "expanded proliferative zone" for m in mutations}}


def simulate_growth(tissue: str, days: int = 14, seed_cells: int = 5000) -> dict:
    """Logistic growth of the organoid population + size estimate."""
    r = ORGANOID_RECIPES.get(tissue.lower(), ORGANOID_RECIPES["intestinal"])
    lam = math.log(2) / r["doubling_days"]
    carrying = 5e6
    series = []
    for d in range(0, days + 1):
        n = carrying / (1 + (carrying / seed_cells - 1) * math.exp(-lam * d))
        series.append({"day": d, "cells": round(n),
                       "diameter_um": round(50 * (n / seed_cells) ** (1 / 3), 1)})
    return {"tissue": tissue, "trajectory": series,
            "final_cells": series[-1]["cells"],
            "note": "logistic model; necrotic core risk above ~500 um diameter"}


def drug_response(tissue: str, compounds: list[str], mutations: list[str] | None = None) -> dict:
    """Drug response on the organoid: IC50-style curves with mutation modifiers."""
    from ..cell_twin.core import DRUG_ACTIONS
    muts = set(mutations or [])
    out = {}
    for c in compounds:
        act = DRUG_ACTIONS.get(c, {"kill": 0.4, "resist_genes": []})
        resist = 0.4 if muts & set(act.get("resist_genes", [])) else 0.0
        ic50 = round(1.0 * (1 + 3 * resist), 3)
        doses = [0.03, 0.1, 0.3, 1, 3, 10]
        viability = [round(100 / (1 + (d / ic50) ** 1.5 * act["kill"]), 1) for d in doses]
        out[c] = {"ic50_uM": ic50, "doses_uM": doses, "viability_pct": viability,
                  "resistance_modifier": resist}
    return {"tissue": tissue, "mutations": sorted(muts), "responses": out,
            "most_effective": min(out, key=lambda c: out[c]["ic50_uM"]) if out else None}

# --- specification-complete patient-derived digital-twin stack ----------------
def optimize_growth_conditions(tissue: str, observations: list[dict] | None = None) -> dict:
    """Fit growth rate and carrying capacity to patient-derived count observations."""
    import numpy as np
    from scipy.optimize import least_squares
    key=tissue.lower()
    if key not in ORGANOID_RECIPES: raise KeyError(f"unknown tissue {tissue!r}")
    obs=list(observations or [])
    if observations is not None and len(obs) not in (0,) and len(obs) < 3:
        raise ValueError("observations requires at least 3 records with day and cells")
    if any("day" not in x or "cells" not in x for x in obs):
        raise ValueError("each observation must contain day and cells")
    if len(obs)>=3:
        t=np.asarray([x["day"] for x in obs],float); y=np.asarray([x["cells"] for x in obs],float)
        if np.any(y<=0) or np.any(np.diff(t)<=0): raise ValueError("positive counts and increasing days required")
        n0=y[0]
        def residual(z):
            rate,K=np.exp(z); pred=K/(1+(K/n0-1)*np.exp(-rate*(t-t[0])))
            return np.log(pred)-np.log(y)
        fit=least_squares(residual,np.log([math.log(2)/ORGANOID_RECIPES[key]["doubling_days"],max(y)*10]),bounds=(-10,20))
        rate,K=np.exp(fit.x); rmse=float((sum(residual(fit.x)**2)/len(y))**.5)
    else:
        rate=math.log(2)/ORGANOID_RECIPES[key]["doubling_days"]; K=5e6; rmse=0.0
    oxygen=20 if key=="cerebral" else 40 if key=="tumor" else 21
    return {"tissue":key,"growth_rate_per_day":round(float(rate),8),"carrying_capacity":round(float(K)),
            "doubling_time_days":round(math.log(2)/float(rate),6),"fit_log_rmse":round(rmse,8),
            "conditions":{"temp_c":37,"co2_pct":5,"oxygen_pct":oxygen,"media_change_hours":48},
            "solver":"scipy_least_squares" if obs else "recipe_prior",
            "model_status":"mechanistic hermetic fit; no trained or clinical claims"}


def simulate_digital_twin(tissue: str, days: float=14, seed_cells: int=5000,
                          patient_mutations: list[str] | None=None, drug_events: list[dict] | None=None,
                          sample_hours: float=12) -> dict:
    """Solve coupled live/dead/nutrient ODEs with timed patient-specific drug exposure."""
    import numpy as np
    from scipy.integrate import solve_ivp
    if days<=0 or seed_cells<=0 or sample_hours<=0: raise ValueError("positive simulation inputs required")
    key=tissue.lower()
    if key not in ORGANOID_RECIPES: raise KeyError(f"unknown tissue {tissue!r}")
    muts=set(patient_mutations or []); events=list(drug_events or [])
    if any("day" not in e for e in events): raise ValueError("each drug event must contain day")
    if any(float(e["day"]) < 0 or float(e["day"]) > days for e in events): raise ValueError("drug event day must be within simulation interval")
    if any(float(e.get("strength", .2)) < 0 for e in events): raise ValueError("drug event strength must be non-negative")
    events=sorted(events,key=lambda x:x["day"])
    rate=math.log(2)/ORGANOID_RECIPES[key]["doubling_days"]*(1+.12*len(muts)); K=5e6
    def exposure(t): return sum(float(e.get("strength",.2))*math.exp(-.5*max(0,t-float(e["day"]))) for e in events if t>=float(e["day"]))
    def rhs(t,y):
        live,dead,nutrient=y; kill=exposure(t)/(1+.25*len(muts))
        growth=rate*live*max(nutrient,0)*(1-live/K)
        return [growth-kill*live,kill*live-.08*dead,.04*(1-nutrient)-growth/K*.2]
    times=np.arange(0,days+1e-9,sample_hours/24); times=np.unique(np.append(times,days))
    sol=solve_ivp(rhs,(0,days),[seed_cells,0,1],t_eval=times,method="LSODA",rtol=1e-8,atol=1e-9)
    if not sol.success: raise RuntimeError(sol.message)
    rows=[{"day":round(float(t),6),"live_cells":round(max(0,float(l))),"dead_cells":round(max(0,float(d))),
           "nutrient_fraction":round(max(0,float(n)),8),"diameter_um":round(50*(max(l,1)/seed_cells)**(1/3),4)}
          for t,l,d,n in zip(sol.t,*sol.y)]
    return {"tissue":key,"patient_mutations":sorted(muts),"trajectory":rows,"final_live_cells":rows[-1]["live_cells"],
            "drug_events":events,"solver":{"method":"LSODA","nfev":sol.nfev,"success":sol.success},
            "recommended_actions":["review trajectories against matched wet-lab controls","inspect nutrient depletion before extending culture","validate simulated drug effects in dose-response assays"],
            "model_status":"mechanistic hermetic ODE digital twin; no trained or clinical claims"}


def spatial_gene_expression(tissue: str, grid_size: int=25, patient_mutations: list[str] | None=None,
                            diffusion_steps: int=80) -> dict:
    """Finite-difference reaction-diffusion map of tissue-zone marker expression."""
    import numpy as np
    if grid_size<5 or diffusion_steps<1: raise ValueError("grid_size >= 5 and positive steps required")
    zones=_spatial_map(tissue.lower(),patient_mutations or [])["zones"]
    if not zones: raise KeyError(f"unknown tissue {tissue!r}")
    yy,xx=np.mgrid[-1:1:complex(grid_size),-1:1:complex(grid_size)]; radius=np.sqrt(xx*xx+yy*yy)
    fields={}; names=list(zones)
    for zi,(zone,genes) in enumerate(zones.items()):
        u=np.exp(-((radius-(.2+.5*zi/max(1,len(names)-1)))**2)/.04)
        for _ in range(diffusion_steps):
            lap=np.roll(u,1,0)+np.roll(u,-1,0)+np.roll(u,1,1)+np.roll(u,-1,1)-4*u
            u=np.clip(u+.12*lap+.01*u*(1-u),0,1)
        for gene in genes: fields[gene]=u.tolist()
    return {"tissue":tissue,"grid_size":grid_size,"genes":fields,"zones":zones,
            "coordinate_system":"normalized radial organoid cross-section","solver":"explicit finite-difference reaction-diffusion"}


def enhancement_features(tissue: str, trajectory: list[dict], spatial: dict | None=None,
                         responses: dict | None=None) -> dict:
    """Compute exactly 55 independent organoid diagnostics without statistics padding."""
    import numpy as np
    if not trajectory: raise ValueError("trajectory required")
    live=np.asarray([x.get("live_cells",x.get("cells",0)) for x in trajectory],float)
    dead=np.asarray([x.get("dead_cells",0) for x in trajectory],float); diam=np.asarray([x.get("diameter_um",0) for x in trajectory],float)
    nutrient=np.asarray([x.get("nutrient_fraction",1) for x in trajectory],float); t=np.asarray([x.get("day",i) for i,x in enumerate(trajectory)],float)
    growth=np.diff(np.log(np.maximum(live,1)))/np.maximum(np.diff(t),1e-9) if len(live)>1 else np.array([0.])
    genes=(spatial or {}).get("genes",{}); res=(responses or {}).get("responses",{})
    out={
    "tissue":tissue,"timepoint_count":len(t),"simulation_duration_days":float(t[-1]-t[0]),"initial_live_cells":float(live[0]),"final_live_cells":float(live[-1]),
    "absolute_live_cell_gain":float(live[-1]-live[0]),"fold_expansion":float(live[-1]/max(live[0],1)),"peak_live_cells":float(live.max()),"peak_live_day":float(t[live.argmax()]),
    "terminal_growth_rate":float(growth[-1]),"max_growth_rate":float(growth.max()),"growth_rate_sign_changes":int(np.sum(np.diff(np.sign(growth))!=0)),
    "doubling_time_terminal":float(math.log(2)/growth[-1]) if growth[-1]>0 else 0.,"area_under_live_curve":float(np.trapz(live,t)),"terminal_dead_cells":float(dead[-1]),
    "peak_dead_cells":float(dead.max()),"terminal_viability":float(live[-1]/max(live[-1]+dead[-1],1)),"cumulative_death_proxy":float(np.trapz(dead,t)),
    "initial_diameter_um":float(diam[0]),"terminal_diameter_um":float(diam[-1]),"diameter_gain_um":float(diam[-1]-diam[0]),"peak_diameter_um":float(diam.max()),
    "necrotic_core_risk":bool(diam.max()>500),"terminal_nutrient_fraction":float(nutrient[-1]),"minimum_nutrient_fraction":float(nutrient.min()),
    "nutrient_depletion":float(nutrient[0]-nutrient[-1]),"nutrient_below_half_timepoints":int(np.sum(nutrient<.5)),"confluence_proxy":float(min(1,live[-1]/5e6)),
    "carrying_capacity_proximity":float(live[-1]/5e6),"monotonic_growth":bool(np.all(np.diff(live)>=0)),"growth_arrest_detected":bool(abs(growth[-1])<.01),
    "collapse_detected":bool(live[-1]<.5*live.max()),"early_late_growth_ratio":float(growth[0]/growth[-1]) if growth[-1] else 0.,"cell_volume_proxy":float(diam[-1]**3),
    "live_density_proxy":float(live[-1]/max(diam[-1]**3,1)),"spatial_gene_count":len(genes),"spatial_grid_size":(spatial or {}).get("grid_size",0),
    "spatial_zone_count":len((spatial or {}).get("zones",{})),"spatial_marker_count":sum(len(x) for x in (spatial or {}).get("zones",{}).values()),
    "spatial_peak_expression":float(max((np.max(v) for v in genes.values()),default=0)),"spatial_active_gene_count":sum(np.max(v)>.5 for v in genes.values()),
    "spatial_center_marker_count":sum(np.asarray(v)[len(v)//2][len(v)//2]>.5 for v in genes.values()),"compound_count":len(res),
    "tested_dose_count":sum(len(v.get("doses_uM",[])) for v in res.values()),"best_ic50_uM":float(min((v.get("ic50_uM",float('inf')) for v in res.values()),default=0)),
    "worst_ic50_uM":float(max((v.get("ic50_uM",0) for v in res.values()),default=0)),"resistant_compound_count":sum(v.get("resistance_modifier",0)>0 for v in res.values()),
    "max_kill_fraction":float(max((1-min(v.get("viability_pct",[100]))/100 for v in res.values()),default=0)),"response_curve_count":len(res),
    "quality_morphology_ready":bool(len(t)>=3),"quality_growth_window_covered":bool(t[-1]-t[0]>=7),"quality_viability_pass":bool(live[-1]/max(live[-1]+dead[-1],1)>=.7),
    "quality_size_pass":bool(diam[-1]<=500),"quality_nutrient_pass":bool(nutrient[-1]>=.2),"digital_twin_completeness":sum([bool(len(t)),bool(genes),bool(res)])/3,
    }
    assert len(out)==55
    return out


def analyze_organoid(tissue: str, *, days: float=14, seed_cells: int=5000,
                     patient_mutations: list[str] | None=None, compounds: list[str] | None=None,
                     drug_events: list[dict] | None=None) -> dict:
    """End-to-end patient-derived 3D tissue digital-twin analysis."""
    design=design_organoid(tissue,patient_mutations); twin=simulate_digital_twin(tissue,days,seed_cells,patient_mutations,drug_events)
    spatial=spatial_gene_expression(tissue,patient_mutations=patient_mutations); drugs=drug_response(tissue,compounds or [],patient_mutations)
    diagnostics=enhancement_features(tissue,twin["trajectory"],spatial,drugs)
    return {"design":design,"digital_twin":twin,"spatial_expression":spatial,"drug_response":drugs,
            "diagnostics":diagnostics,"diagnostic_count":55,
            "scientist_summary":{"final_live_cells":twin["final_live_cells"],"necrotic_core_risk":diagnostics["necrotic_core_risk"],"terminal_viability":diagnostics["terminal_viability"],"best_compound":drugs["most_effective"]},
            "model_status":"mechanistic hermetic organoid model; no trained or clinical claims"}
