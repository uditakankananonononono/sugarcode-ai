from __future__ import annotations
import numpy as _np
_trapz = getattr(_np, "trapezoid", None) or _np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0
import math
import random

PHAGE_LIBRARY = {
    "phiKZ": {"targets": ["Pseudomonas_aeruginosa"], "receptor": "LPS",
              "burst": 180, "latent_min": 50},
    "T4": {"targets": ["Escherichia_coli"], "receptor": "LPS/OmpC", "burst": 150, "latent_min": 25},
    "K": {"targets": ["Staphylococcus_aureus"], "receptor": "wall_teichoic", "burst": 90, "latent_min": 40},
    "phiAB6": {"targets": ["Acinetobacter_baumannii"], "receptor": "capsule", "burst": 120, "latent_min": 35},
    "vB_EfaS": {"targets": ["Enterococcus_faecalis"], "receptor": "Epa", "burst": 60, "latent_min": 45},
    "M13": {"targets": ["Escherichia_coli"], "receptor": "F_pilus", "burst": 0, "latent_min": 0},
    # Distinct-receptor lytic isolates make cocktail optimization executable.
    "T7": {"targets": ["Escherichia_coli"], "receptor": "LPS", "burst": 110, "latent_min": 17},
    "lambda_vir": {"targets": ["Escherichia_coli"], "receptor": "LamB", "burst": 95, "latent_min": 40},
    "LUZ19": {"targets": ["Pseudomonas_aeruginosa"], "receptor": "type_IV_pilus", "burst": 120, "latent_min": 24},
}
RESISTANCE_MECHANISMS = {
    "LPS": "LPS modification (waaL mutation)",
    "LPS/OmpC": "OmpC loss (porin down-regulation)",
    "wall_teichoic": "WTA glycosylation change (tarM)",
    "capsule": "capsule overproduction",
    "Epa": "epa locus phase variation",
    "F_pilus": "plasmid loss",
    "LamB": "LamB receptor loss or modification",
    "type_IV_pilus": "type IV pilus loss or retraction defect",
}
RECEPTOR_REDUNDANCY = {"LPS": ["capsule", "Epa"], "OmpC": ["capsule"],
                       "capsule": ["LPS", "wall_teichoic"], "Epa": ["LPS"],
                       "wall_teichoic": ["capsule"], "F_pilus": ["LPS/OmpC"],
                       "LamB": ["LPS", "OmpC"], "type_IV_pilus": ["LPS"]}


def match_phages(pathogen: str) -> dict:
    """Match a pathogen to phages in the library; flag receptor-based resistance
    routes and suggest complementary pairings."""
    hits = {name: spec for name, spec in PHAGE_LIBRARY.items() if pathogen in spec["targets"]}
    if not hits:
        raise KeyError(f"no phage for {pathogen}; library covers "
                       f"{sorted({t for s in PHAGE_LIBRARY.values() for t in s['targets']})}")
    entries = []
    for name, spec in hits.items():
        rec = spec["receptor"]
        entries.append({
            "phage": name, "receptor": rec, "burst_size": spec["burst"],
            "latent_min": spec["latent_min"],
            "lytic": spec["burst"] > 0,
            "resistance_risk": RESISTANCE_MECHANISMS[rec],
            "complementary_receptors": RECEPTOR_REDUNDANCY.get(rec.split("/")[0], []),
        })
    entries.sort(key=lambda e: -e["burst_size"])
    return {
        "pathogen": pathogen,
        "matches": entries,
        "best": entries[0],
        "monitoring": ["qPCR bacterial load 0/6/24/48h",
                       "plaque assay on therapy-sample isolates (resistance emergence)",
                       "receptor gene sequencing of breakthrough isolates"],
    }


def evolve_cocktail(pathogen: str, rounds: int = 3, seed: int = 42) -> dict:
    """Model cocktail composition to suppress resistance: pair phages with
    non-overlapping receptors, iterate against simulated escape mutants."""
    rng = random.Random(seed)
    matched = match_phages(pathogen)["matches"]
    lytic = [m for m in matched if m["lytic"]]
    cocktail, receptors = [], set()
    for m in lytic:
        rec = m["receptor"].split("/")[0]
        if rec not in receptors:
            cocktail.append(m["phage"])
            receptors.add(rec)
    if len(cocktail) < 2 and len(lytic) > 1:
        cocktail = [m["phage"] for m in lytic[:2]]
    history = []
    kill = 0.85
    for r in range(rounds):
        escape_rate = round(0.3 ** len(cocktail) * (0.8 + 0.4 * rng.random()), 4)
        kill = round(min(0.999, kill + 0.05 * len(cocktail)), 4)
        history.append({"round": r + 1, "kill_fraction": kill,
                        "escape_mutant_rate": escape_rate})
    return {
        "pathogen": pathogen, "cocktail": cocktail,
        "receptor_coverage": sorted(receptors),
        "evolution_history": history,
        "final_escape_rate": history[-1]["escape_mutant_rate"],
        "strategy": ("non-overlapping receptor targets force simultaneous multi-locus "
                     "mutations for escape - escape rate falls exponentially with cocktail size"),
        "personalized_match": "re-screen patient isolate against cocktail before dosing",
    }

# --- exact host-phage coevolution and cocktail optimization ------------------
def validate_phage_parameters(parameters: dict) -> dict:
    """Validate a quantitative phage-host experiment configuration."""
    defaults={"bacteria":1e7,"phage":1e6,"growth_rate_per_h":.8,"carrying_capacity":1e10,"adsorption_ml_per_h":1e-9,"burst_size":100,"latent_h":.5,"mutation_rate":1e-7,"hours":48}
    p={**defaults,**dict(parameters or {})}
    positive=("bacteria","phage","growth_rate_per_h","carrying_capacity","adsorption_ml_per_h","burst_size","latent_h","hours")
    if any(not isinstance(p[x],(int,float)) or p[x]<=0 for x in positive): raise ValueError(f"{', '.join(positive)} must be positive numbers")
    if not 0<=p["mutation_rate"]<=1: raise ValueError("mutation_rate must be in [0, 1]")
    if p["bacteria"]>p["carrying_capacity"]: raise ValueError("initial bacteria cannot exceed carrying_capacity")
    return {k:float(v) for k,v in p.items()}


def simulate_coevolution(parameters: dict | None=None, *, sample_minutes: float=15) -> dict:
    """Solve susceptible, resistant, infected, and phage delay dynamics."""
    import numpy as np
    _trapz = getattr(np, "trapezoid", None) or np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0
    from scipy.integrate import solve_ivp
    p=validate_phage_parameters(parameters or {})
    if sample_minutes<=0: raise ValueError("sample_minutes must be positive")
    # I is infected cells; lysis is first-order at inverse latent period.
    def rhs(_,y):
        S,R,I,P=y; total=S+R+I; logistic=max(0,1-total/p["carrying_capacity"]); infections=p["adsorption_ml_per_h"]*S*P; mutations=p["mutation_rate"]*p["growth_rate_per_h"]*S*logistic
        return [p["growth_rate_per_h"]*S*logistic-infections-mutations,.75*p["growth_rate_per_h"]*R*logistic+mutations,infections-I/p["latent_h"],p["burst_size"]*I/p["latent_h"]-infections-.1*P]
    times=np.arange(0,p["hours"]+1e-9,sample_minutes/60); times=np.unique(np.append(times,p["hours"])); sol=solve_ivp(rhs,(0,p["hours"]),[p["bacteria"],0,0,p["phage"]],t_eval=times,method="BDF",rtol=1e-8,atol=1e-4)
    if not sol.success: raise RuntimeError(sol.message)
    rows=[]
    for t,S,R,I,P in zip(sol.t,*sol.y):
        vals=[max(0,float(x)) for x in (S,R,I,P)]; total=sum(vals[:3]); rows.append({"hour":float(t),"susceptible":vals[0],"resistant":vals[1],"infected":vals[2],"phage":vals[3],"total_bacteria":total,"resistant_fraction":vals[1]/max(total,1e-30)})
    return {"parameters":p,"trajectory":rows,"final_bacterial_load":rows[-1]["total_bacteria"],"final_resistant_fraction":rows[-1]["resistant_fraction"],"solver":{"method":"BDF","nfev":sol.nfev,"success":sol.success},"model_status":"mechanistic hermetic coevolution ODE; no therapeutic efficacy claim"}


def optimize_cocktail(pathogen: str, isolate_susceptibility: dict[str,float], *, max_phages: int=3, resistance_penalty: float=.4) -> dict:
    """Exactly optimize cocktail membership over the available library."""
    import itertools
    if max_phages<1: raise ValueError("max_phages must be positive")
    hits=[n for n,s in PHAGE_LIBRARY.items() if pathogen in s["targets"] and s["burst"]>0]
    if not hits: raise ValueError(f"no lytic phages available for {pathogen}")
    unknown=set(isolate_susceptibility)-set(hits)
    if unknown: raise ValueError(f"susceptibility supplied for unavailable phages: {sorted(unknown)}")
    if any(not 0<=float(v)<=1 for v in isolate_susceptibility.values()): raise ValueError("susceptibility values must be in [0, 1]")
    scored=[]
    for size in range(1,min(max_phages,len(hits))+1):
        for combo in itertools.combinations(hits,size):
            susceptibility=1-math.prod(1-float(isolate_susceptibility.get(x,0)) for x in combo); receptors={PHAGE_LIBRARY[x]["receptor"].split('/')[0] for x in combo}; redundancy=len(receptors)/len(combo); escape=math.prod(max(1e-6,1-float(isolate_susceptibility.get(x,0))) for x in combo); score=susceptibility+.25*redundancy-resistance_penalty*escape-.03*size
            scored.append({"cocktail":list(combo),"score":round(score,8),"predicted_kill_fraction":round(susceptibility,8),"receptor_count":len(receptors),"receptor_redundancy":round(redundancy,8),"escape_probability":round(escape,10),"phage_count":size})
    scored.sort(key=lambda x:(-x["score"],x["phage_count"],x["cocktail"]))
    return {"pathogen":pathogen,"ranking":scored,"selected":scored[0],"solver":"exact_subset_enumeration","evaluated_cocktails":len(scored)}


def enhancement_features(simulation: dict, optimization: dict) -> dict:
    """Compute 51 coevolution/cocktail diagnostics from case outputs."""
    import numpy as np
    r=simulation["trajectory"]; t=np.array([x["hour"] for x in r]); S=np.array([x["susceptible"] for x in r]); R=np.array([x["resistant"] for x in r]); I=np.array([x["infected"] for x in r]); P=np.array([x["phage"] for x in r]); B=np.array([x["total_bacteria"] for x in r]); F=np.array([x["resistant_fraction"] for x in r]); sel=optimization["selected"]; rank=optimization["ranking"]
    out={"duration_h":float(t[-1]),"timepoint_count":len(t),"initial_bacterial_load":float(B[0]),"final_bacterial_load":float(B[-1]),"bacterial_fold_change":float(B[-1]/B[0]),"bacterial_log10_change":float(np.log10(max(B[-1],1))-np.log10(max(B[0],1))),"minimum_bacterial_load":float(B.min()),"minimum_bacterial_hour":float(t[B.argmin()]),"maximum_bacterial_load":float(B.max()),"maximum_bacterial_hour":float(t[B.argmax()]),"bacterial_auc":float(_trapz(B,t)),"initial_susceptible":float(S[0]),"final_susceptible":float(S[-1]),"susceptible_fold_change":float(S[-1]/max(S[0],1)),"peak_infected":float(I.max()),"peak_infected_hour":float(t[I.argmax()]),"infected_auc":float(_trapz(I,t)),"initial_resistant":float(R[0]),"final_resistant":float(R[-1]),"peak_resistant":float(R.max()),"peak_resistant_hour":float(t[R.argmax()]),"final_resistant_fraction":float(F[-1]),"peak_resistant_fraction":float(F.max()),"resistance_half_fraction_hour":float(t[np.argmax(F>=.5)]) if np.any(F>=.5) else float(t[-1]),"initial_phage":float(P[0]),"final_phage":float(P[-1]),"phage_fold_change":float(P[-1]/max(P[0],1)),"peak_phage":float(P.max()),"peak_phage_hour":float(t[P.argmax()]),"phage_auc":float(_trapz(P,t)),"phage_to_bacteria_initial":float(P[0]/B[0]),"phage_to_bacteria_final":float(P[-1]/max(B[-1],1)),"solver_evaluations":simulation["solver"]["nfev"],"cocktails_evaluated":optimization["evaluated_cocktails"],"selected_score":sel["score"],"selected_phage_count":sel["phage_count"],"selected_kill_fraction":sel["predicted_kill_fraction"],"selected_receptor_count":sel["receptor_count"],"selected_receptor_redundancy":sel["receptor_redundancy"],"selected_escape_probability":sel["escape_probability"],"best_score_margin":float(rank[0]["score"]-rank[1]["score"]) if len(rank)>1 else 0.,"best_kill_margin":float(rank[0]["predicted_kill_fraction"]-rank[1]["predicted_kill_fraction"]) if len(rank)>1 else 0.,"single_phage_candidate_count":sum(x["phage_count"]==1 for x in rank),"multi_phage_candidate_count":sum(x["phage_count"]>1 for x in rank),"lowest_ranked_score":rank[-1]["score"],"lowest_escape_probability":min(x["escape_probability"] for x in rank),"highest_escape_probability":max(x["escape_probability"] for x in rank),"kill_fraction_range":max(x["predicted_kill_fraction"] for x in rank)-min(x["predicted_kill_fraction"] for x in rank),"score_range":rank[0]["score"]-rank[-1]["score"],"suppression_fraction_at_nadir":float(1-B.min()/B[0]),"rebound_fraction_from_nadir":float((B[-1]-B.min())/max(B.min(),1))}
    assert len(out)==51
    return out


def design_phage_therapy(pathogen: str, isolate_susceptibility: dict[str,float], parameters: dict | None=None) -> dict:
    """Create a lab-actionable cocktail and coevolution monitoring package."""
    opt=optimize_cocktail(pathogen,isolate_susceptibility); selected=opt["selected"]; base=dict(parameters or {}); base["burst_size"]=sum(PHAGE_LIBRARY[x]["burst"] for x in selected["cocktail"])/len(selected["cocktail"]); sim=simulate_coevolution(base); diag=enhancement_features(sim,opt)
    return {"optimization":opt,"simulation":sim,"diagnostics":diag,"diagnostic_count":51,"modification_suggestions":[{"phage":x,"receptor":PHAGE_LIBRARY[x]["receptor"],"action":"retain distinct receptor coverage"} for x in selected["cocktail"]],"monitoring_plan":["time-kill assay at 0/6/24/48 h","plaque assay on breakthrough isolates","sequence receptor loci","measure endotoxin and sterility before translational work"]}
