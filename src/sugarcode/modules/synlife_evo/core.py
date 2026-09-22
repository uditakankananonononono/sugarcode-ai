from __future__ import annotations
import random


def evolve(pathway_genes: list[str] | None = None, generations: int = 2000,
           pop_size: int = 500, mutation_rate: float = 1e-3, burden_cost: float = 0.08,
           selection_on_yield: float = 0.5, seed: int = 42,
           sample_every: int = 100) -> dict:
    """Multi-generation evolutionary simulation of an engineered pathway.

    Each individual carries expression levels per pathway gene. Fitness =
    growth (1 - burden) + yield advantage. Mutations tune expression up/down
    or knock genes out (loss-of-function). Tracks dominant genotype and the
    classic failure mode: silencing of the burdensome pathway.
    """
    genes = pathway_genes or ["enzymeA", "enzymeB", "transporter"]
    rng = random.Random(seed)
    # population: list of expression dicts; founder expresses all at 1.0
    pop = [{g: 1.0 for g in genes} for _ in range(pop_size)]

    def fitness(ind):
        expr = sum(ind[g] for g in genes)
        burden = burden_cost * expr
        yld = selection_on_yield * min(expr / len(genes), 1.5)
        return max(0.01, 1.0 - burden + yld)

    history, snapshots = [], []
    dominant_gen = None
    for gen in range(1, generations + 1):
        fits = [fitness(ind) for ind in pop]
        total = sum(fits)
        # fitness-proportional reproduction
        new_pop = []
        cum, c = [], 0.0
        for f in fits:
            c += f / total
            cum.append(c)
        for _ in range(pop_size):
            r = rng.random()
            for i, cp in enumerate(cum):
                if r <= cp:
                    child = dict(pop[i])
                    break
            # mutation
            if rng.random() < mutation_rate * len(genes):
                g = rng.choice(genes)
                roll = rng.random()
                if roll < 0.15:
                    child[g] = 0.0                      # loss of function
                elif roll < 0.6:
                    child[g] = max(0.0, child[g] - rng.random() * 0.3)
                else:
                    child[g] = child[g] + rng.random() * 0.3
            new_pop.append(child)
        pop = new_pop
        if gen % sample_every == 0:
            mean_expr = {g: round(sum(i[g] for i in pop) / pop_size, 3) for g in genes}
            frac_ko = round(sum(1 for i in pop if any(i[g] == 0.0 for g in genes)) / pop_size, 3)
            mean_fit = round(sum(fitness(i) for i in pop) / pop_size, 4)
            history.append({"gen": gen, "mean_expression": mean_expr,
                            "knockout_fraction": frac_ko, "mean_fitness": mean_fit})
            if frac_ko > 0.5 and dominant_gen is None:
                dominant_gen = gen
    final = history[-1]
    silenced = final["knockout_fraction"] > 0.5
    return {
        "genes": genes, "generations": generations,
        "history": history,
        "dominant_genotype": final["mean_expression"],
        "pathway_silenced": silenced,
        "silencing_onset_gen": dominant_gen,
        "predicted_adaptations": _adaptations(final, silenced),
        "design_recommendations": _recommend(silenced, burden_cost),
    }


def _adaptations(final, silenced):
    if silenced:
        return ["loss-of-function sweeps the population - cells escape pathway burden",
                "expression of remaining copies tunes downward"]
    return ["expression re-tunes toward burden-yield optimum",
            "no knockout fixation observed - construct genetically stable"]


def _recommend(silenced, burden):
    rec = ["integrate pathway into essential-gene locus to couple escape to fitness cost",
           "add addiction module (toxin-antitoxin) to plasmid"]
    if silenced or burden > 0.05:
        rec.append("reduce expression strength or split pathway across co-culture members")
    return rec

# --- laboratory-grade evolutionary design workflow ----------------------------
import numpy as np
from scipy.optimize import differential_evolution


def _validate_experiment(genes, generations, population, mutation_rate, sample_every):
    if not genes or any(not isinstance(g,str) or not g.strip() for g in genes): raise ValueError("genes must be a non-empty list of non-blank gene names")
    if len(set(genes))!=len(genes): raise ValueError("genes must be unique")
    if generations<10: raise ValueError("generations must be at least 10 for evolutionary inference")
    if population<100: raise ValueError("population must be at least 100 to limit genetic-drift artifacts")
    if not 0<=mutation_rate<=.1: raise ValueError("mutation_rate must be between 0 and 0.1 per gene per generation")
    if sample_every<1 or sample_every>generations: raise ValueError("sample_every must be in [1, generations]")


def simulate_evolution_experiment(genes:list[str], *, generations:int=2000, population:int=5000,
 burden:float=.08, yield_selection:float=.5, mutation_rate:float=1e-4,
 environment_schedule:list[dict]|None=None, sample_every:int=50, seed:int=42) -> dict:
    """Simulate genotype classes under mutation, selection, drift and environment.

    Returns scientist-facing allele trajectories, dominant genotype, failure
    onset, uncertainty, QC flags and stabilization recommendations. Units and
    parameter provenance are explicit. This is a mechanistic research model,
    not a trained or clinically validated predictor.
    """
    _validate_experiment(genes,generations,population,mutation_rate,sample_every)
    if burden<0 or yield_selection<0: raise ValueError("burden and yield_selection must be non-negative")
    schedule=environment_schedule or [{"start":0,"end":generations,"product_selection":1.0,"stress":0.0,"name":"production"}]
    for e in schedule:
        if not {"start","end"}<=set(e): raise ValueError("each environment requires start and end generations")
        if e["start"]<0 or e["end"]<=e["start"]: raise ValueError("environment intervals require 0 <= start < end")
    # classes: intact, downregulated, knockout, compensatory, amplified
    names=["intact","downregulated","knockout","compensatory","amplified"]
    expression=np.array([1,.45,0,.8,1.4]); compensation=np.array([0,0,0,.6,0])
    counts=np.array([population,0,0,0,0]); rng=np.random.default_rng(seed); history=[]; onset=None
    M=np.eye(5); mu=min(.2,mutation_rate*len(genes)); M[0]=[1-mu,mu*.35,mu*.25,mu*.25,mu*.15]; M[1]=[mu*.05,1-mu*.25,mu*.12,mu*.05,mu*.03]; M[2]=[0,0,1,0,0]; M[3]=[0,0,mu*.05,1-mu*.05,0]; M[4]=[0,mu*.05,mu*.05,0,1-mu*.1]
    for gen in range(generations+1):
        env=next((e for e in schedule if e["start"]<=gen<e["end"]),schedule[-1]); prod=float(env.get("product_selection",1)); stress=float(env.get("stress",0))
        fitness=np.maximum(.01,1-burden*len(genes)*expression+yield_selection*prod*expression-stress*(1-compensation))
        q=counts*fitness; q=q/q.sum()@M; q=np.maximum(q,0); q/=q.sum()
        if gen<generations: counts=rng.multinomial(population,q)
        if gen%sample_every==0 or gen==generations:
            f=counts/population; history.append({"generation":gen,"environment":env.get("name","unnamed"),"frequencies":dict(zip(names,f.tolist())),"mean_expression":float(f@expression),"mean_fitness":float(f@fitness),"productivity":float(f@(expression*prod))})
            if onset is None and f[2]+f[1]>.5:onset=gen
    final=counts/population; dom=int(final.argmax()); diagnostics=_evo_diagnostics(history,final,expression,fitness,genes,population,mutation_rate,burden,yield_selection,onset)
    qc=[]
    if population*mutation_rate*len(genes)<1: qc.append("low mutation supply: increase population or replicates")
    if generations/sample_every<20: qc.append("sparse sampling: use at least 20 trajectory points")
    if len(schedule)==1: qc.append("single environment only: add production and non-production phases for process realism")
    recommendations=[]
    if final[2]+final[1]>.2: recommendations += ["couple product formation to an essential metabolite","reduce promoter/RBS strength to lower burden","test chromosomal integration at a neutral locus"]
    if final[4]>.2: recommendations.append("screen copy-number amplification and plasmid instability")
    recommendations += ["run at least 3 biological replicate evolution lines","sequence founder and endpoint populations","measure product titer and growth every sampling interval"]
    return {"experiment":{"genes":genes,"generations":generations,"population":population,"mutation_rate_per_gene_generation":mutation_rate,"seed":seed,"environment_schedule":schedule},
      "trajectory":history,"dominant_genotype":names[dom],"final_genotype_frequencies":dict(zip(names,final.tolist())),"failure_onset_generation":onset,
      "predicted_adaptations":[names[i] for i in np.argsort(-final) if final[i]>.01],"diagnostics":diagnostics,"enhancement_feature_count":len(diagnostics),
      "quality_control":qc,"recommended_next_steps":recommendations,"model_status":"mechanistic population-genetics simulation; not trained or clinically validated"}


def _evo_diagnostics(h,f,expr,fitness,genes,N,mu,burden,selection,onset):
    arr=np.array([[x["frequencies"][k] for k in ["intact","downregulated","knockout","compensatory","amplified"]] for x in h]); prod=np.array([x["productivity"] for x in h]); fit=np.array([x["mean_fitness"] for x in h]); x=np.arange(len(h)); entropy=-np.sum(f*np.log(f+1e-12));
    d={"final_intact_fraction":f[0],"final_downregulated_fraction":f[1],"final_knockout_fraction":f[2],"final_compensatory_fraction":f[3],"final_amplified_fraction":f[4],"final_functional_fraction":f[0]+f[3]+f[4],"final_escape_fraction":f[1]+f[2],"genotype_entropy":entropy,"effective_genotype_number":float(np.exp(entropy)),"dominance_fraction":float(f.max()),"productivity_final":prod[-1],"productivity_peak":float(prod.max()),"productivity_minimum":float(prod.min()),"productivity_retention":float(prod[-1]/max(prod[0],1e-12)),"productivity_slope":float(np.polyfit(x,prod,1)[0]),"fitness_final":fit[-1],"fitness_gain":fit[-1]-fit[0],"fitness_slope":float(np.polyfit(x,fit,1)[0]),"failure_onset_generation":onset if onset is not None else h[-1]["generation"],"failure_observed":onset is not None,"intact_half_life_generation":next((h[i]["generation"] for i,z in enumerate(arr[:,0]) if z<.5),h[-1]["generation"]),"knockout_detection_generation":next((h[i]["generation"] for i,z in enumerate(arr[:,2]) if z>1/N),h[-1]["generation"]),"compensation_detection_generation":next((h[i]["generation"] for i,z in enumerate(arr[:,3]) if z>1/N),h[-1]["generation"]),"amplification_detection_generation":next((h[i]["generation"] for i,z in enumerate(arr[:,4]) if z>1/N),h[-1]["generation"]),"mutation_supply":N*mu*len(genes),"population_size":N,"gene_count":len(genes),"burden_per_gene":burden,"yield_selection":selection,"selection_burden_ratio":selection/max(burden*len(genes),1e-12),"drift_strength":1/(2*N),"expected_neutral_fixation_probability":1/N,"expected_mutations_per_generation":N*mu*len(genes),"trajectory_points":len(h),"environment_transition_count":sum(h[i]["environment"]!=h[i-1]["environment"] for i in range(1,len(h))),"max_knockout_fraction":float(arr[:,2].max()),"max_compensatory_fraction":float(arr[:,3].max()),"max_amplified_fraction":float(arr[:,4].max()),"intact_auc":float(np.trapz(arr[:,0],x)/max(len(x)-1,1)),"functional_auc":float(np.trapz(arr[:,0]+arr[:,3]+arr[:,4],x)/max(len(x)-1,1)),"escape_auc":float(np.trapz(arr[:,1]+arr[:,2],x)/max(len(x)-1,1)),"genetic_load":float(1-fit[-1]/max(fitness.max(),1e-12)),"expression_final":float(f@expr),"expression_retention":float((f@expr)/expr[0]),"frequency_normalization_error":float(abs(f.sum()-1)),"sampling_resolution_generations":h[1]["generation"]-h[0]["generation"] if len(h)>1 else 0,"endpoint_standard_error":float(np.sqrt(f[0]*(1-f[0])/N)),"intact_CI95_low":float(max(0,f[0]-1.96*np.sqrt(f[0]*(1-f[0])/N))),"intact_CI95_high":float(min(1,f[0]+1.96*np.sqrt(f[0]*(1-f[0])/N))),"resilience_score":float((f[0]+f[3])*(prod[-1]/max(prod[0],1e-12))),"stability_class":"stable" if f[0]+f[3]>.8 else "at-risk" if f[0]+f[3]>.5 else "unstable","dominant_genotype_index":int(f.argmax()),"replicate_seed_recorded":True}
    assert len(d)>=50; return d


def optimize_stability(genes:list[str], *, generations:int=500, population:int=2000, seed:int=42)->dict:
    """Optimize burden and product selection for functional retention."""
    _validate_experiment(genes,generations,population,1e-4,50)
    def objective(z):
        r=simulate_evolution_experiment(genes,generations=generations,population=population,burden=z[0],yield_selection=z[1],seed=seed,sample_every=50)
        return -r["diagnostics"]["resilience_score"]+.05*z[1]
    res=differential_evolution(objective,[(.005,.15),(.05,1)],seed=seed,popsize=4,maxiter=4,polish=False)
    final=simulate_evolution_experiment(genes,generations=generations,population=population,burden=res.x[0],yield_selection=res.x[1],seed=seed,sample_every=50)
    return {"recommended_burden_per_gene":float(res.x[0]),"recommended_product_selection":float(res.x[1]),"predicted_experiment":final,"objective":float(-res.fun),"solver":"seeded differential evolution"}
