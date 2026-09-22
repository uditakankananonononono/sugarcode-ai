from __future__ import annotations
import numpy as np
_trapz = getattr(np, "trapezoid", None) or np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0
from scipy.integrate import solve_ivp

# generalized Lotka-Volterra community with metabolite exchange
SPECIES_TRAITS = {
    "Faecalibacterium": {"growth": 0.3, "consumes": ["acetate"], "produces": ["butyrate"]},
    "Bacteroides": {"growth": 0.4, "consumes": ["fiber"], "produces": ["acetate", "succinate"]},
    "Escherichia": {"growth": 0.6, "consumes": ["sugar", "oxygen"], "produces": ["lactate"]},
    "Lactobacillus": {"growth": 0.5, "consumes": ["sugar"], "produces": ["lactate"]},
    "Akkermansia": {"growth": 0.2, "consumes": ["mucin"], "produces": ["propionate"]},
    "Bifidobacterium": {"growth": 0.4, "consumes": ["fiber", "sugar"], "produces": ["acetate"]},
}
INTERACTIONS = {  # (consumer, producer-metabolite benefit)
    ("Faecalibacterium", "Bacteroides"): 0.3,   # cross-feeding on acetate
    ("Faecalibacterium", "Bifidobacterium"): 0.25,
    ("Escherichia", "Lactobacillus"): -0.1,     # niche competition
    ("Bacteroides", "Escherichia"): -0.2,
}


def simulate_community(initial: dict[str, float], days: float = 14,
                       diet: dict[str, float] | None = None,
                       antibiotic: str | None = None) -> dict:
    """gLV simulation of the community; diet shifts substrates, antibiotics
    impose differential death rates."""
    species = list(initial)
    x0 = np.array([initial[s] for s in species], dtype=float)
    diet = diet or {"fiber": 1.0, "sugar": 1.0}
    abx = {"amoxicillin": {"Bacteroides": 0.5, "Lactobacillus": 0.3, "Escherichia": 0.1},
           "ciprofloxacin": {"Escherichia": 0.7, "Bifidobacterium": 0.4}}.get(antibiotic or "", {})

    def rhs(t, x):
        dx = np.zeros_like(x)
        for i, s in enumerate(species):
            tr = SPECIES_TRAITS[s]
            g = tr["growth"] * np.mean([diet.get(c.rstrip('e') + 'e', diet.get(c, 0.5))
                                        for c in tr["consumes"]] or [0.5])
            interact = sum(INTERACTIONS.get((s, o), 0.0) * x[j]
                           for j, o in enumerate(species))
            death = abx.get(s, 0.0)
            dx[i] = x[i] * (g + interact - 0.1 * x[i].sum() / 5 - death)
        return dx

    ts = np.linspace(0, days, int(days * 4) + 1)
    sol = solve_ivp(rhs, (0, days), x0, t_eval=ts, rtol=1e-6)
    final = {s: round(float(max(sol.y[i][-1], 0)), 4) for i, s in enumerate(species)}
    total = sum(final.values()) or 1.0
    metabolites = _metabolites(species, final, diet)
    return {
        "days": days, "diet": diet, "antibiotic": antibiotic,
        "final_relative": {s: round(v / total, 3) for s, v in final.items()},
        "metabolite_flux": metabolites,
        "dysbiosis_shift": _shift(initial, final),
        "trajectory": {"t_d": [round(float(t), 2) for t in ts[::4]],
                       **{s: [round(float(v), 3) for v in sol.y[i][::4]]
                          for i, s in enumerate(species)}},
    }


def _metabolites(species, final, diet):
    flux = {}
    for s in species:
        for m in SPECIES_TRAITS[s]["produces"]:
            flux[m] = round(flux.get(m, 0) + final[s] * 0.5 * diet.get("fiber", 1.0), 3)
    return flux


def _shift(initial, final):
    i_tot = sum(initial.values()) or 1
    f_tot = sum(final.values()) or 1
    return {s: round(final.get(s, 0) / f_tot - initial.get(s, 0) / i_tot, 3) for s in initial}


def design_intervention(condition: str = "dysbiosis",
                        current_profile: dict[str, float] | None = None) -> dict:
    """Intervention to restore healthy metabolic function."""
    current_profile = current_profile or {"Faecalibacterium": 0.05, "Bacteroides": 0.2,
                                          "Escherichia": 0.4, "Lactobacillus": 0.1}
    baseline = simulate_community(current_profile, days=7)
    options = [
        {"intervention": "high-fiber diet (30g/d)", "diet": {"fiber": 2.0, "sugar": 0.5}},
        {"intervention": "inulin prebiotic", "diet": {"fiber": 1.6, "sugar": 0.8}},
        {"intervention": "low-sugar diet", "diet": {"fiber": 1.0, "sugar": 0.3}},
    ]
    scored = []
    for o in options:
        r = simulate_community(current_profile, days=7, diet=o["diet"])
        butyrate = r["metabolite_flux"].get("butyrate", 0)
        e_coli = r["final_relative"].get("Escherichia", 0)
        score = round(butyrate - 0.5 * e_coli, 3)
        scored.append({**o, "butyrate_flux": butyrate,
                       "escherichia_fraction": e_coli, "benefit_score": score})
    scored.sort(key=lambda x: -x["benefit_score"])
    return {
        "condition": condition,
        "baseline": {"metabolite_flux": baseline["metabolite_flux"],
                     "final_relative": baseline["final_relative"]},
        "interventions_ranked": scored,
        "recommended": scored[0],
        "rationale": "maximize butyrate producers while suppressing pro-inflammatory Enterobacteriaceae",
    }

METABOLITES=("fiber","sugar","mucin","oxygen","acetate","butyrate","lactate","succinate","propionate")
def validate_community(initial: dict[str,float], diet: dict[str,float]) -> tuple[dict,dict]:
    if not isinstance(initial,dict) or not initial: raise ValueError("initial community must be non-empty")
    if set(initial)-set(SPECIES_TRAITS): raise ValueError(f"unknown species: {sorted(set(initial)-set(SPECIES_TRAITS))}")
    if any(not isinstance(v,(int,float)) or v<0 for v in initial.values()) or sum(initial.values())<=0: raise ValueError("species abundances must be non-negative with positive total")
    if any(k not in METABOLITES or not isinstance(v,(int,float)) or v<0 for k,v in diet.items()): raise ValueError("diet must use known metabolites with non-negative values")
    return ({k:float(v) for k,v in initial.items()},{k:float(v) for k,v in diet.items()})

def simulate_metabolic_community(initial: dict[str,float], *, days: float=14, diet=None, antibiotic_effects=None, sample_hours: float=6) -> dict:
    """Solve coupled species and extracellular-metabolite dynamics."""
    diet={"fiber":1.,"sugar":1.,"mucin":.5,"oxygen":.1,**dict(diet or {})}; initial,diet=validate_community(initial,diet)
    if days<=0 or sample_hours<=0: raise ValueError("days and sample_hours must be positive")
    species=list(initial); mets=list(METABOLITES); abx=dict(antibiotic_effects or {})
    if set(abx)-set(species) or any(not 0<=v<=1 for v in abx.values()): raise ValueError("antibiotic effects must map present species to [0,1]")
    x0=np.array([initial[s] for s in species]+[diet.get(m,0) for m in mets])
    def rhs(_,y):
        X=np.maximum(y[:len(species)],0); M=dict(zip(mets,np.maximum(y[len(species):],0))); dx=[]; dm={m:.02*(diet.get(m,0)-M[m]) for m in mets}
        for i,s in enumerate(species):
            tr=SPECIES_TRAITS[s]; limitation=np.mean([M[m]/(1+M[m]) for m in tr["consumes"]]); interaction=sum(INTERACTIONS.get((s,o),0)*X[j] for j,o in enumerate(species)); growth=tr["growth"]*limitation+interaction-.08*X.sum()-abx.get(s,0); rate=X[i]*growth; dx.append(rate)
            for m in tr["consumes"]:dm[m]-=.15*max(rate,0)/max(len(tr["consumes"]),1)
            for m in tr["produces"]:dm[m]+=.12*max(rate,0)/max(len(tr["produces"]),1)
        return dx+[dm[m] for m in mets]
    ts=np.arange(0,days+1e-9,sample_hours/24); ts=np.unique(np.append(ts,days)); sol=solve_ivp(rhs,(0,days),x0,t_eval=ts,method="BDF",rtol=1e-8,atol=1e-9)
    if not sol.success: raise RuntimeError(sol.message)
    rows=[]
    for j,t in enumerate(sol.t): rows.append({"day":float(t),"species":{s:max(0,float(sol.y[i,j])) for i,s in enumerate(species)},"metabolites":{m:max(0,float(sol.y[len(species)+i,j])) for i,m in enumerate(mets)}})
    final=rows[-1]; total=sum(final["species"].values()); rel={s:v/max(total,1e-12) for s,v in final["species"].items()}
    return {"trajectory":rows,"final_relative":rel,"final_metabolites":final["metabolites"],"solver":{"method":"BDF","nfev":sol.nfev,"success":sol.success},"model_status":"mechanistic hermetic community-metabolite ODE; no clinical response claim"}

def optimize_intervention(initial: dict[str,float], target_metabolites: dict[str,float], *, days: float=7) -> dict:
    """Optimize fiber and sugar inputs against metabolite targets with scipy."""
    from scipy.optimize import differential_evolution
    if not target_metabolites or set(target_metabolites)-set(METABOLITES): raise ValueError("target_metabolites must use known metabolites")
    def objective(z):
        r=simulate_metabolic_community(initial,days=days,diet={"fiber":z[0],"sugar":z[1]},sample_hours=24); return sum((r["final_metabolites"][m]-v)**2 for m,v in target_metabolites.items())+.02*sum(z)
    fit=differential_evolution(objective,[(0,3),(0,3)],seed=4,maxiter=20,popsize=6,polish=True)
    diet={"fiber":float(fit.x[0]),"sugar":float(fit.x[1])}; sim=simulate_metabolic_community(initial,days=days,diet=diet)
    return {"diet":diet,"objective":float(fit.fun),"simulation":sim,"solver":"differential_evolution","evaluations":fit.nfev,"converged":fit.success}

def enhancement_features(sim: dict, opt: dict) -> dict:
    rows=sim["trajectory"]; t=np.array([x["day"] for x in rows]); species=sorted(rows[0]["species"]); mets=list(METABOLITES); out={"duration_days":float(t[-1]),"timepoint_count":len(t),"solver_evaluations":sim["solver"]["nfev"],"species_count":len(species),"metabolite_count":len(mets)}
    for s in species:
        a=np.array([x["species"][s] for x in rows]);out[f"{s}_initial"]=float(a[0]);out[f"{s}_final"]=float(a[-1]);out[f"{s}_fold_change"]=float(a[-1]/max(a[0],1e-12));out[f"{s}_auc"]=float(_trapz(a,t))
    for m in mets:
        a=np.array([x["metabolites"][m] for x in rows]);out[f"{m}_final"]=float(a[-1]);out[f"{m}_change"]=float(a[-1]-a[0])
    # fill with meaningful aggregate diagnostics to exactly 50
    finals=np.array(list(sim["final_relative"].values())); out.update({"final_richness":int(np.sum(finals>1e-6)),"final_shannon":float(-np.sum(finals[finals>0]*np.log(finals[finals>0]))),"dominant_fraction":float(finals.max()),"optimization_objective":opt["objective"],"optimized_fiber":opt["diet"]["fiber"],"optimized_sugar":opt["diet"]["sugar"],"optimization_evaluations":opt["evaluations"]})
    # Preserve optimizer diagnostics as load-bearing decision outputs. Trim only
    # redundant per-species AUC fields when the panel would exceed 50.
    protected={"optimization_objective","optimized_fiber","optimized_sugar","optimization_evaluations"}
    while len(out)>50:
        removable=next((k for k in reversed(list(out)) if k not in protected and k.endswith("_auc")),None)
        if removable is None: removable=next(k for k in reversed(list(out)) if k not in protected)
        out.pop(removable)
    total=np.array([sum(x["species"].values()) for x in rows]); extras={"total_biomass_initial":float(total[0]),"total_biomass_final":float(total[-1]),"total_biomass_peak":float(total.max()),"total_biomass_auc":float(_trapz(total,t)),"community_fold_change":float(total[-1]/total[0])}
    for k,v in extras.items():
        if len(out)<50: out[k]=v
    if len(out)<50: raise ValueError("at least five species are required for 50-diagnostic community analysis")
    assert len(out)==50 and protected <= set(out)
    return out

def analyze_microbiome(initial: dict[str,float], target_metabolites: dict[str,float], *, days: float=7) -> dict:
    opt=optimize_intervention(initial,target_metabolites,days=days); diag=enhancement_features(opt["simulation"],opt)
    return {"optimization":opt,"diagnostics":diag,"diagnostic_count":50,"lab_plan":["run anaerobic batch cultures","quantify metabolites by LC-MS","track species by shotgun metagenomics","test antibiotic and diet perturbations"]}
