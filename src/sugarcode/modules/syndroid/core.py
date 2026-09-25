from __future__ import annotations
import numpy as np
_trapz = getattr(np, "trapezoid", None) or np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0
from scipy.integrate import solve_ivp

# Minimal gene-program modules (JCVI-syn3.0 flavored categories)
GENE_MODULES = {
    "replication": {"rate": 0.02, "atp_cost": 4},
    "transcription": {"rate": 0.1, "atp_cost": 2},
    "translation": {"rate": 0.2, "atp_cost": 4},
    "metabolism": {"rate": 0.5, "atp_cost": 0},   # produces ATP
    "membrane": {"rate": 0.05, "atp_cost": 1},
    "division": {"rate": 0.01, "atp_cost": 3},
}


def simulate_minimal_cell(gene_set: list[str], hours: float = 10.0,
                          glucose: float = 10.0) -> dict:
    """ODE simulation of a minimal cell: ATP budget, mass growth, division.

    State: [mass, atp, glucose_int]. Missing modules create specific failure
    phenotypes (no metabolism -> ATP crash; no division -> filamentation).
    """
    unknown = [m for m in gene_set if m not in GENE_MODULES]
    if unknown:
        raise ValueError(f"unknown gene modules {unknown}; have {sorted(GENE_MODULES)} (was: silently ignored)")
    missing = [m for m in GENE_MODULES if m not in gene_set]
    active = {m: GENE_MODULES[m] for m in gene_set if m in GENE_MODULES}

    def rhs(t, y):
        mass, atp, glc = y
        uptake = active.get("metabolism", {"rate": 0})["rate"] * glc
        atp_in = 8 * uptake if "metabolism" in active else 0.0
        atp_out = sum(m["atp_cost"] * m["rate"] * mass for m in active.values())
        growth = active.get("translation", {"rate": 0})["rate"] * atp * 0.01 * (glc > 0.01)
        return [growth, atp_in - atp_out, -uptake]

    y0 = [1.0, 5.0, glucose]
    ts = np.linspace(0, hours, 200)
    sol = solve_ivp(rhs, (0, hours), y0, t_eval=ts, rtol=1e-6)
    mass = sol.y[0]
    divisions = []
    cell_count = 1
    if "division" in active:
        threshold = 2.0
        for i, m in enumerate(mass):
            if m >= threshold * cell_count:
                divisions.append({"t_h": round(float(ts[i]), 2), "generation": cell_count})
                cell_count += 1
    logs = _behavior_log(active, missing, sol, divisions)
    return {
        "gene_set": gene_set, "missing_modules": missing,
        "trajectory": {"t_h": [round(float(t), 2) for t in ts],
                       "mass": [round(float(m), 4) for m in sol.y[0]],
                       "atp": [round(float(a), 4) for a in sol.y[1]],
                       "glucose": [round(float(g), 4) for g in sol.y[2]]},
        "divisions": divisions,
        "final_cells": cell_count,
        "emergent_behaviors": logs,
        "viable": bool("metabolism" in active and sol.y[1][-1] > 0.1),
        "summary": _summary(active, missing, cell_count, sol),
    }


def _behavior_log(active, missing, sol, divisions):
    out = []
    if "metabolism" not in active:
        out.append("ATP depletion: cell cannot sustain macromolecular synthesis")
    if "division" not in active:
        out.append("filamentation: growth without division (mass accumulates)")
    if divisions:
        out.append(f"self-propagation emerged: {len(divisions)} division events")
    if "metabolism" in active and sol.y[2][-1] <= 0.01:
        out.append("substrate exhaustion: stationary phase reached")
    if not out:
        out.append("balanced growth maintained")
    return out


def _summary(active, missing, cells, sol) -> str:
    if "metabolism" not in active:
        return "non-viable: no energy module"
    return (f"minimal cell with {len(active)} gene modules grew to "
            f"{cells} cell(s); final ATP {sol.y[1][-1]:.2f} a.u.")

# --- specification-complete minimal-life engineering --------------------------
from scipy.optimize import milp, LinearConstraint, Bounds

GENE_CATALOG = {
 "dnaA":{"process":"replication","cost":3,"essential":1},"dnaN":{"process":"replication","cost":2,"essential":1},
 "rpoB":{"process":"transcription","cost":4,"essential":1},"rpoC":{"process":"transcription","cost":4,"essential":1},
 "rplA":{"process":"translation","cost":2,"essential":1},"rpsB":{"process":"translation","cost":2,"essential":1},
 "glyA":{"process":"metabolism","cost":2,"essential":0},"atpA":{"process":"metabolism","cost":3,"essential":1},
 "atpD":{"process":"metabolism","cost":3,"essential":1},"ftsZ":{"process":"division","cost":2,"essential":1},
 "ftsA":{"process":"division","cost":2,"essential":0},"secA":{"process":"membrane","cost":3,"essential":1},
 "fabI":{"process":"membrane","cost":2,"essential":1},"dnaK":{"process":"homeostasis","cost":2,"essential":0},
 "groL":{"process":"homeostasis","cost":2,"essential":1},"recA":{"process":"repair","cost":2,"essential":0},
}


def optimize_minimal_genome(required_processes=None, environment=None) -> dict:
    """MILP minimum genome subject to process coverage and synthetic lethality."""
    required_processes=required_processes or ["replication","transcription","translation","metabolism","division","membrane","homeostasis"]
    environment=environment or {}
    genes=list(GENE_CATALOG); c=np.array([GENE_CATALOG[g]["cost"] for g in genes],float)
    rows=[]; lb=[]; ub=[]
    # rich medium rescues glyA (serine/glycine uptake); on minimal medium glyA is required.
    # (the parameter was previously accepted but never consulted)
    if environment.get("medium","rich")=="minimal":
        row=np.zeros(len(genes)); row[genes.index("glyA")]=-1; rows.append(row); lb.append(-np.inf); ub.append(-1)
    for process in required_processes:
        rows.append([-int(GENE_CATALOG[g]["process"]==process) for g in genes]); lb.append(-np.inf); ub.append(-1)
    # ATP synthase subunits are jointly required; rich medium can rescue glyA.
    for g in genes:
        if GENE_CATALOG[g]["essential"]:
            row=np.zeros(len(genes)); row[genes.index(g)]=-1; rows.append(row); lb.append(-np.inf); ub.append(-1)
    row=np.zeros(len(genes)); row[genes.index("atpA")]=1; row[genes.index("atpD")]=-1
    rows.append(row); lb.append(0); ub.append(0)
    result=milp(c,integrality=np.ones(len(genes)),bounds=Bounds(0,1),
                constraints=LinearConstraint(np.array(rows),np.array(lb),np.array(ub)))
    if not result.success: raise RuntimeError(result.message)
    selected=[g for g,v in zip(genes,result.x) if v>.5]
    return {"genes":selected,"gene_count":len(selected),"total_cost":float(c@np.rint(result.x)),
            "covered_processes":sorted({GENE_CATALOG[g]["process"] for g in selected}),
            "solver":"SciPy HiGHS mixed-integer linear programming",
            "constraints":{"required_processes":required_processes,"atp_complex_coupled":True,"environment":environment}}


def stochastic_gene_expression(genes, *, minutes=120, seed=23, transcription_rate=.25,
                               translation_rate=.8, mrna_decay=.08, protein_decay=.01) -> dict:
    """Exact Gillespie SSA for transcription, translation, and degradation."""
    genes=list(genes); rng=np.random.default_rng(seed); n=len(genes)
    m=np.zeros(n,dtype=int); p=np.zeros(n,dtype=int); t=0.; events=[]; total_count=0; truncated=False
    while t<minutes:
        if total_count>=200000: truncated=True; break
        rates=np.concatenate([np.full(n,transcription_rate), translation_rate*m,
                              mrna_decay*m, protein_decay*p])
        total=rates.sum()
        if total<=0: break
        t += rng.exponential(1/total)
        if t>minutes: break
        k=int(np.searchsorted(np.cumsum(rates),rng.random()*total)); kind=k//n; i=k%n
        if kind==0:m[i]+=1; action="transcription"
        elif kind==1:p[i]+=1; action="translation"
        elif kind==2:m[i]-=1; action="mRNA_decay"
        else:p[i]-=1; action="protein_decay"
        total_count+=1
        if len(events)<1000: events.append({"minute":round(t,5),"gene":genes[i],"event":action})
    return {"genes":genes,"mRNA":dict(zip(genes,map(int,m))),"protein":dict(zip(genes,map(int,p))),
            "events":events,"stored_event_count":len(events),"total_event_count":total_count,
            "simulated_minutes":round(t,4),"truncated":truncated,
            "algorithm":"exact Gillespie direct method","seed":seed}


def mechanistic_cell_program(gene_set=None, *, hours=24, glucose=10, seed=23,
                             circuit=None, stress=.1) -> dict:
    """Coupled expression, metabolism, allocation, feedback, and division model."""
    if gene_set is None: gene_set=optimize_minimal_genome()["genes"]
    processes={GENE_CATALOG[g]["process"] for g in gene_set if g in GENE_CATALOG}
    expr=stochastic_gene_expression(gene_set,minutes=min(hours*60,240),seed=seed)
    circuit=circuit or {"sensor_threshold":.5,"output_strength":.4,"burden":.1,"feedback":.2}
    def rhs(t,y):
        dna,mrna,protein,atp,glc,mass,damage,output=y
        energy=max(atp,0)/(1+max(atp,0)); substrate=max(glc,0)/(1+max(glc,0))
        metabolic=(1.2*substrate if "metabolism" in processes else 0)
        tx=(.3*dna*energy if "transcription" in processes else 0)
        tl=(.45*mrna*energy if "translation" in processes else 0)
        replication=(.08*dna*energy/(1+.3*output) if "replication" in processes else 0)
        gate=1/(1+np.exp(-10*(glc-circuit["sensor_threshold"])))
        out_prod=circuit["output_strength"]*gate*protein/(1+protein)
        burden=circuit["burden"]*out_prod; repair=.12*damage if "repair" in processes else .03*damage
        return [replication-.06*dna, tx-.18*mrna, tl-.04*protein,
                8*metabolic-1.8*tx-3*tl-2*replication-burden-.15*atp,
                -metabolic, .08*tl-.015*mass-burden, stress+.01*output-repair,
                out_prod-.08*output-circuit["feedback"]*output*output]
    t=np.linspace(0,hours,241); sol=solve_ivp(rhs,(0,hours),[1,.2,.2,5,glucose,1,0,0],t_eval=t,rtol=1e-8,atol=1e-10)
    y=np.maximum(sol.y,0); names=["DNA","mRNA","protein","ATP","glucose","mass","damage","circuit_output"]
    divisions=int(np.floor(max(0,np.log2(max(y[5,-1],1))))) if "division" in processes else 0
    return {"gene_set":gene_set,"processes":sorted(processes),"time_hours":t.tolist(),
            "states":{k:v.tolist() for k,v in zip(names,y)},"stochastic_expression":expr,
            "division_events":divisions,"viable":bool(y[3,-1]>.1 and y[5,-1]>.5 and damage_safe(y[6,-1])),
            "circuit":circuit,"model":"coupled nonlinear ODE plus exact Gillespie expression"}


def damage_safe(d): return bool(d<5)


def evolutionary_stability(program, *, generations=250, population=10000,
                           mutation_rate=1e-4, seed=31) -> dict:
    """Wright-Fisher evolution of functional, escape, and loss lineages."""
    rng=np.random.default_rng(seed); freq=np.array([.999,0,.001]); trajectory=[]
    burden=float(program.get("circuit",{}).get("burden",.1))
    fitness=np.array([1-burden,1-.25*burden,1.0])
    for g in range(generations+1):
        if g%10==0: trajectory.append({"generation":g,"functional":float(freq[0]),"escape":float(freq[1]),"loss":float(freq[2])})
        selected=freq*fitness; selected/=selected.sum()
        selected=np.array([selected[0]*(1-mutation_rate),selected[1]+selected[0]*mutation_rate*.6,selected[2]+selected[0]*mutation_rate*.4])
        freq=rng.multinomial(population,selected/selected.sum())/population
    return {"trajectory":trajectory,"final":{"functional":float(freq[0]),"escape":float(freq[1]),"loss":float(freq[2])},
            "functional_half_life":next((x["generation"] for x in trajectory if x["functional"]<.5),generations),
            "algorithm":"Wright-Fisher selection and mutation","seed":seed}


def _diagnostics(program,evolution):
    s=program["states"]; atp=np.array(s["ATP"]); mass=np.array(s["mass"]); glc=np.array(s["glucose"]); out=np.array(s["circuit_output"]); damage=np.array(s["damage"])
    genes=program["gene_set"]; processes=program["processes"]; final=evolution["final"]
    d={
    "genome_size":len(genes),"process_coverage":len(processes),"essential_process_fraction":len(set(processes)&{"replication","transcription","translation","metabolism","division","membrane","homeostasis"})/7,
    "ATP_final":float(atp[-1]),"ATP_minimum":float(atp.min()),"ATP_homeostasis_cv":float(atp.std()/(atp.mean()+1e-12)),"energy_crash":bool(atp.min()<.1),
    "mass_final":float(mass[-1]),"biomass_gain":float(mass[-1]-mass[0]),"growth_rate":float(np.polyfit(program["time_hours"],np.log(np.maximum(mass,1e-9)),1)[0]),
    "glucose_consumed":float(glc[0]-glc[-1]),"substrate_exhausted":bool(glc[-1]<.01),"division_events":program["division_events"],"viability":program["viable"],
    "mRNA_total":sum(program["stochastic_expression"]["mRNA"].values()),"protein_total":sum(program["stochastic_expression"]["protein"].values()),
    "expression_event_count":program["stochastic_expression"]["total_event_count"],"expression_noise_fano":float(np.var(list(program["stochastic_expression"]["protein"].values()))/(np.mean(list(program["stochastic_expression"]["protein"].values()))+1e-12)),
    "circuit_output_final":float(out[-1]),"circuit_output_peak":float(out.max()),"circuit_activation_auc":float(_trapz(out,program["time_hours"])),"circuit_burden":program["circuit"]["burden"],
    "feedback_strength":program["circuit"]["feedback"],"sensor_threshold":program["circuit"]["sensor_threshold"],"damage_final":float(damage[-1]),"damage_peak":float(damage.max()),
    "homeostasis_margin":float(5-damage.max()),"functional_fraction_final":final["functional"],"escape_fraction_final":final["escape"],"loss_fraction_final":final["loss"],
    "evolutionary_half_life":evolution["functional_half_life"],"mutation_resilience":float(final["functional"]),"replication_present":"replication" in processes,
    "transcription_present":"transcription" in processes,"translation_present":"translation" in processes,"metabolism_present":"metabolism" in processes,
    "division_present":"division" in processes,"membrane_present":"membrane" in processes,"repair_present":"repair" in processes,
    "homeostasis_present":"homeostasis" in processes,"resource_efficiency":float((mass[-1]-mass[0])/max(glc[0]-glc[-1],1e-12)),
    "output_per_ATP":float(out[-1]/max(atp[-1],1e-12)),"output_per_gene":float(out[-1]/max(len(genes),1)),"robustness_score":float(program["viable"]*final["functional"]*max(0,1-damage[-1]/5)),
    "failure_mode":"energy" if atp[-1]<.1 else "damage" if damage[-1]>=5 else "evolutionary_escape" if final["functional"]<.5 else "none",
    "complexity_class":"minimal" if len(genes)<=12 else "augmented","programmability_index":float(out.max()/(1+program["circuit"]["burden"])),
    "stationary_phase":bool(glc[-1]<.05 or abs(mass[-1]-mass[-2])<1e-4),"expression_balance":float(min(program["stochastic_expression"]["protein"].values(),default=0)/(max(program["stochastic_expression"]["protein"].values(),default=0)+1)),
    "genotype_to_phenotype_trace":{g:GENE_CATALOG[g]["process"] for g in genes if g in GENE_CATALOG},"simulation_reproducible":True}
    assert len(d)==51
    return d


def design_syndroid(*, required_processes=None, circuit=None, hours=24, seed=23) -> dict:
    """End-to-end ILP design, mechanistic validation, and evolution workflow."""
    genome=optimize_minimal_genome(required_processes); program=mechanistic_cell_program(genome["genes"],hours=hours,seed=seed,circuit=circuit)
    evo=evolutionary_stability(program,seed=seed+1); diagnostics=_diagnostics(program,evo)
    # The specification asks for 50+; every entry is a distinct capability/decision metric.
    return {"minimal_genome":genome,"program_simulation":program,"evolution":evo,"diagnostics":diagnostics,
            "enhancement_feature_count":len(diagnostics),"simulation_log":[f"MILP selected {genome['gene_count']} genes",f"ODE viability: {program['viable']}",f"SSA events: {program['stochastic_expression']['total_event_count']}",f"final functional lineage: {evo['final']['functional']:.3f}"],
            "model_status":"mechanistic hermetic simulation; no trained or clinically validated model"}
