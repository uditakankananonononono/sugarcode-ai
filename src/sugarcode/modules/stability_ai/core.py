from __future__ import annotations
import math


def stability_forecast(construct: dict, generations: int = 200) -> dict:
    """Simulate construct loss: plasmid segregational loss + mutational drift.

    construct: {"mode": "plasmid"|"genomic", "burden": 0..1, "size_kb": float,
                "toxic": bool}
    Plasmid loss modeled per generation (loss rate grows with burden);
    mutational inactivation as Poisson process over functional target size.
    """
    mode = construct.get("mode", "plasmid")
    burden = min(max(construct.get("burden", 0.3), 0.0), 1.0)
    size_kb = construct.get("size_kb", 5.0)
    toxic = construct.get("toxic", False)

    loss_rate = (0.002 if mode == "plasmid" else 0.00005) * (1 + 4 * burden)
    mut_rate_per_kb = 1e-4 * (2.0 if toxic else 1.0)
    func_fraction = 1.0
    series = []
    for g in range(0, generations + 1, 10):
        plasmid_retention = (1 - loss_rate) ** g
        mut_survival = math.exp(-mut_rate_per_kb * size_kb * g)
        func = plasmid_retention * mut_survival
        series.append({"generation": g, "functional_fraction": round(func, 4)})
    half_life = next((s["generation"] for s in series if s["functional_fraction"] < 0.5),
                     generations)
    final = series[-1]["functional_fraction"]
    score = round(final * 100, 1)
    return {
        "construct": construct,
        "trajectory": series,
        "functional_half_life_generations": half_life,
        "stability_score": score,
        "failure_modes": _failure_modes(mode, burden, toxic),
        "stability_class": "robust" if score > 80 else "moderate" if score > 50 else "fragile",
    }


def _failure_modes(mode: str, burden: float, toxic: bool) -> list[str]:
    out = []
    if mode == "plasmid":
        out.append("segregational plasmid loss without selection")
    if burden > 0.5:
        out.append("metabolic burden selects for expression-loss mutants")
    if toxic:
        out.append("product toxicity drives suppressor mutations")
    out.append("mutational drift in cargo region over long passaging")
    return out

import hashlib

def validate_construct(construct: dict) -> dict:
    if not isinstance(construct,dict): raise ValueError("construct must be a mapping")
    mode=construct.get("mode","plasmid"); burden=construct.get("burden"); size=construct.get("size_kb")
    if mode not in {"plasmid","genomic"}: raise ValueError("mode must be plasmid or genomic")
    if not isinstance(burden,(int,float)) or not 0<=burden<=1: raise ValueError("burden must be in [0, 1]")
    if not isinstance(size,(int,float)) or size<=0: raise ValueError("size_kb must be positive")
    copy=float(construct.get("copy_number",20 if mode=="plasmid" else 1)); expression=float(construct.get("expression_load",burden));
    if copy<=0 or expression<0: raise ValueError("copy_number must be positive and expression_load non-negative")
    return {**construct,"mode":mode,"burden":float(burden),"size_kb":float(size),"copy_number":copy,"expression_load":expression,"toxic":bool(construct.get("toxic",False))}


def stochastic_drift(construct: dict, *, generations: int=200, population: int=10000, replicates: int=64, seed: int=42) -> dict:
    """Run exact seeded Wright-Fisher simulations of functional construct loss."""
    import numpy as np
    c=validate_construct(construct)
    if generations<1 or population<10 or replicates<2: raise ValueError("generations >=1, population >=10, replicates >=2 required")
    rng=np.random.default_rng(seed); freq=np.ones(replicates); traj=[]; base_loss=(.002 if c["mode"]=="plasmid" else .00005)*(1+4*c["burden"]); mutation=1e-4*c["size_kb"]*(2 if c["toxic"] else 1); selection=.08*c["expression_load"]
    for g in range(generations+1):
        if g%max(1,generations//50)==0 or g==generations: traj.append({"generation":g,"mean_functional_fraction":float(freq.mean()),"minimum":float(freq.min()),"maximum":float(freq.max()),"extinct_replicates":int(np.sum(freq==0))})
        if g==generations: break
        after=freq*(1-base_loss-mutation); p=after*(1-selection)/(1-after+after*(1-selection)+1e-30); freq=rng.binomial(population,np.clip(p,0,1),size=replicates)/population
    return {"construct":c,"trajectory":traj,"terminal_fractions":freq.tolist(),"terminal_mean":float(freq.mean()),"terminal_survival_probability":float(np.mean(freq>.5)),"extinction_probability":float(np.mean(freq==0)),"parameters":{"loss_rate":base_loss,"mutation_rate":mutation,"selection_against_function":selection},"seed":seed,"model_status":"mechanistic hermetic Wright-Fisher simulation; no production-lot prediction"}


def optimize_stability(construct: dict, *, generations: int=200) -> dict:
    """Evaluate engineering modifications and rank stability improvement."""
    c=validate_construct(construct); interventions={"baseline":{},"genomic_integration":{"mode":"genomic","copy_number":1},"burden_reduction":{"burden":c["burden"]*.5,"expression_load":c["expression_load"]*.6},"toxin_removal":{"toxic":False},"size_reduction":{"size_kb":c["size_kb"]*.7}}
    rows=[]
    for name,change in interventions.items():
        design={**c,**change}; result=stability_forecast(design,generations); rows.append({"intervention":name,"construct":design,"stability_score":result["stability_score"],"half_life_generations":result["functional_half_life_generations"],"improvement":result["stability_score"]-stability_forecast(c,generations)["stability_score"]})
    rows.sort(key=lambda x:(-x["stability_score"],x["intervention"]))
    return {"ranking":rows,"selected":rows[0],"evaluated_interventions":len(rows)}


def enhancement_features(simulation: dict, optimization: dict) -> dict:
    import numpy as np
    tr=simulation["trajectory"]; g=np.array([x["generation"] for x in tr]); mean=np.array([x["mean_functional_fraction"] for x in tr]); mi=np.array([x["minimum"] for x in tr]); ma=np.array([x["maximum"] for x in tr]); extinct=np.array([x["extinct_replicates"] for x in tr]); terminal=np.array(simulation["terminal_fractions"]); rank=optimization["ranking"]; scores=np.array([x["stability_score"] for x in rank]); improve=np.array([x["improvement"] for x in rank]); p=simulation["parameters"]; sel=optimization["selected"]
    out={"generation_count":int(g[-1]),"sampled_timepoint_count":len(g),"initial_mean_functional_fraction":float(mean[0]),"terminal_mean_functional_fraction":float(mean[-1]),"mean_fraction_change":float(mean[-1]-mean[0]),"minimum_mean_fraction":float(mean.min()),"mean_fraction_auc":float(np.trapz(mean,g)),"mean_decline_per_generation":float((mean[0]-mean[-1])/g[-1]),"initial_replicate_minimum":float(mi[0]),"terminal_replicate_minimum":float(mi[-1]),"terminal_replicate_maximum":float(ma[-1]),"terminal_replicate_range":float(ma[-1]-mi[-1]),"initial_extinct_replicates":int(extinct[0]),"terminal_extinct_replicates":int(extinct[-1]),"first_extinction_generation":int(g[np.argmax(extinct>0)]) if np.any(extinct>0) else int(g[-1]),"terminal_distribution_mean":float(terminal.mean()),"terminal_distribution_min":float(terminal.min()),"terminal_distribution_max":float(terminal.max()),"terminal_distribution_range":float(np.ptp(terminal)),"terminal_survival_probability":simulation["terminal_survival_probability"],"extinction_probability":simulation["extinction_probability"],"terminal_above_90pct_count":int(np.sum(terminal>.9)),"terminal_below_half_count":int(np.sum(terminal<.5)),"loss_rate":p["loss_rate"],"mutation_rate":p["mutation_rate"],"selection_against_function":p["selection_against_function"],"combined_hazard":p["loss_rate"]+p["mutation_rate"]+p["selection_against_function"],"intervention_count":optimization["evaluated_interventions"],"selected_stability_score":sel["stability_score"],"selected_half_life_generations":sel["half_life_generations"],"selected_improvement":sel["improvement"],"score_min":float(scores.min()),"score_max":float(scores.max()),"score_range":float(np.ptp(scores)),"score_margin":float(scores[0]-scores[1]),"improvement_min":float(improve.min()),"improvement_max":float(improve.max()),"improvement_range":float(np.ptp(improve)),"positive_intervention_count":int(np.sum(improve>0)),"neutral_intervention_count":int(np.sum(improve==0)),"baseline_score":next(x["stability_score"] for x in rank if x["intervention"]=="baseline"),"integration_score":next(x["stability_score"] for x in rank if x["intervention"]=="genomic_integration"),"burden_reduction_score":next(x["stability_score"] for x in rank if x["intervention"]=="burden_reduction"),"toxin_removal_score":next(x["stability_score"] for x in rank if x["intervention"]=="toxin_removal"),"size_reduction_score":next(x["stability_score"] for x in rank if x["intervention"]=="size_reduction"),"initial_population_replicates":len(terminal),"construct_burden":simulation["construct"]["burden"],"construct_size_kb":simulation["construct"]["size_kb"],"construct_copy_number":simulation["construct"]["copy_number"],"construct_expression_load":simulation["construct"]["expression_load"]}
    assert len(out)==50
    return out


def analyze_stability(construct: dict, *, generations: int=200, population: int=10000, replicates: int=64, seed: int=42) -> dict:
    """Return a long-run stability forecast, intervention ranking, and QC plan."""
    sim=stochastic_drift(construct,generations=generations,population=population,replicates=replicates,seed=seed); opt=optimize_stability(construct,generations=generations); diag=enhancement_features(sim,opt)
    return {"simulation":sim,"optimization":opt,"diagnostics":diag,"diagnostic_count":50,"failure_modes":_failure_modes(sim["construct"]["mode"],sim["construct"]["burden"],sim["construct"]["toxic"]),"validation_plan":["run serial-passage retention assay","sequence endpoint populations","measure expression burden","test without selection at process scale"]}

# --- molecular, biochemical, environmental, and CNV stability v2 ------------
def sequence_risk_map(sequence: str, *, window: int=30) -> dict:
    """Map repeat, GC-skew, hairpin and homopolymer susceptibility by window."""
    seq=sequence.upper().replace(" ","")
    if not seq or set(seq)-set("ACGT"): raise ValueError("sequence must be non-empty DNA using A/C/G/T")
    if window<10 or window>len(seq): raise ValueError("window must be between 10 and sequence length")
    rows=[]
    for start in range(0,len(seq)-window+1,max(1,window//3)):
        s=seq[start:start+window]; gc=(s.count("G")+s.count("C"))/len(s); skew=(s.count("G")-s.count("C"))/max(s.count("G")+s.count("C"),1); hom=max(len(x) for x in __import__('re').findall(r"A+|C+|G+|T+",s)); repeats=sum(s.count(s[i:i+3])-1 for i in range(len(s)-2)); rc=s.translate(str.maketrans("ACGT","TGCA"))[::-1]; hairpin=max((k for k in range(4,min(13,len(s)//2+1)) if any(s[i:i+k] in rc for i in range(len(s)-k+1))),default=0); risk=.25*abs(gc-.5)*2+.2*abs(skew)+.2*min(1,hom/8)+.2*min(1,repeats/20)+.15*min(1,hairpin/12)
        rows.append({"start":start,"end":start+window,"gc_fraction":gc,"gc_skew":skew,"max_homopolymer":hom,"repeat_score":repeats,"hairpin_stem_bp":hairpin,"risk":risk})
    rows.sort(key=lambda x:-x["risk"])
    return {"sequence_length":len(seq),"window":window,"regions":rows,"vulnerable_regions":[x for x in rows if x["risk"]>=.45],"maximum_risk":rows[0]["risk"],"mean_risk":sum(x["risk"] for x in rows)/len(rows)}


def molecular_stability_profile(construct: dict, environment: dict | None=None) -> dict:
    """Combine DNA mutation modes, CNV, folding, aggregation, and chemical decay."""
    c=validate_construct(construct); env={"temperature_C":37,"pH":7,"oxidative_stress":0,"metabolite_half_life_h":72,"cofactor_half_life_h":96,**dict(environment or {})}
    if not 0<=env["oxidative_stress"]<=1 or not 0<env["pH"]<14 or not -20<=env["temperature_C"]<=80: raise ValueError("environment requires oxidative_stress [0,1], pH (0,14), temperature_C [-20,80]")
    seqmap=sequence_risk_map(c.get("sequence","ATGC"*30),window=min(30,len(c.get("sequence","ATGC"*30))))
    stress=abs(env["temperature_C"]-37)/20+abs(env["pH"]-7)/3+env["oxidative_stress"]
    point=1e-8*(1+4*env["oxidative_stress"])*(1+seqmap["mean_risk"]); insertion=2e-9*(1+seqmap["maximum_risk"]*5); deletion=3e-9*(1+seqmap["maximum_risk"]*7); cnv_rate=(2e-4 if c["mode"]=="plasmid" else 1e-5)*(1+stress); folding_energy=-.08*len(c.get("protein_sequence","")) + 3*stress; aggregation=1/(1+math.exp(-(folding_energy+5)/3)); degradation_rate=.01*math.exp(.25*max(0,env["temperature_C"]-37)+.2*abs(env["pH"]-7)); metabolite_survival=math.exp(-math.log(2)*24/env["metabolite_half_life_h"]); cofactor_survival=math.exp(-math.log(2)*24/env["cofactor_half_life_h"])
    return {"sequence_risk_map":seqmap,"mutation_rates":{"point":point,"insertion":insertion,"deletion":deletion},"cnv_rate_per_generation":cnv_rate,"environment":env,"environmental_stress_index":stress,"protein":{"folding_energy_proxy":folding_energy,"aggregation_probability":aggregation,"degradation_rate_per_h":degradation_rate},"biochemical":{"metabolite_24h_survival":metabolite_survival,"cofactor_24h_survival":cofactor_survival}}


def stochastic_drift_v2(construct: dict, *, environment: dict | None=None, generations: int=200, population: int=10000, replicates: int=64, seed: int=42) -> dict:
    """Wright-Fisher simulation with mutation classes, CNV, and environmental selection."""
    import numpy as np
    c=validate_construct(construct); mol=molecular_stability_profile(c,environment)
    if generations<1 or population<10 or replicates<2: raise ValueError("generations >=1, population >=10, replicates >=2 required")
    rng=np.random.default_rng(seed); functional=np.ones(replicates); copy=np.full(replicates,c["copy_number"]); rows=[]; rates=mol["mutation_rates"]; mut=sum(rates.values())*c["size_kb"]*1000; envsel=.03*mol["environmental_stress_index"]+.05*c["expression_load"]
    for g in range(generations+1):
        if g%max(1,generations//50)==0 or g==generations: rows.append({"generation":g,"functional_mean":float(functional.mean()),"copy_number_mean":float(copy.mean()),"copy_number_min":float(copy.min()),"copy_number_max":float(copy.max()),"extinct":int(np.sum(functional==0))})
        if g==generations:break
        copy=np.maximum(0,copy+rng.choice([-1,0,1],replicates,p=[mol["cnv_rate_per_generation"]/2,1-mol["cnv_rate_per_generation"],mol["cnv_rate_per_generation"]/2]))
        retention=1-np.exp(-copy/max(c["copy_number"],1)); p=np.clip(functional*(1-mut)*(1-envsel)*retention,0,1); functional=rng.binomial(population,p)/population
    return {"construct":c,"molecular_profile":mol,"trajectory":rows,"terminal_functional":functional.tolist(),"terminal_copy_number":copy.tolist(),"model_status":"mechanistic hermetic Wright-Fisher/CNV/environment model; no production prediction"}


def optimize_stability_v2(construct: dict, environment: dict | None=None, *, generations: int=100) -> dict:
    """Rank redundancy, kill-switch, selection, integration, and burden strategies."""
    c=validate_construct(construct); interventions={"baseline":{},"genomic_integration":{"mode":"genomic","copy_number":1},"burden_reduction":{"burden":c["burden"]*.5,"expression_load":c["expression_load"]*.6},"sequence_redundancy":{"copy_number":c["copy_number"]*2,"burden":min(1,c["burden"]*1.15)},"kill_switch":{"toxic":False,"burden":min(1,c["burden"]+.05)},"selection_pressure":{"copy_number":max(c["copy_number"],5),"expression_load":c["expression_load"]*.9}}
    rows=[]
    for name,change in interventions.items():
        design={**c,**change}; sim=stochastic_drift_v2(design,environment=environment,generations=generations,population=2000,replicates=24,seed=13); terminal=sum(sim["terminal_functional"])/len(sim["terminal_functional"]); safety_bonus=.05 if name=="kill_switch" else 0; rows.append({"intervention":name,"terminal_functional":terminal,"terminal_copy_number_mean":sum(sim["terminal_copy_number"])/len(sim["terminal_copy_number"]),"score":terminal+safety_bonus,"construct":design})
    rows.sort(key=lambda x:-x["score"]); return {"ranking":rows,"selected":rows[0],"evaluated_interventions":len(rows)}


def analyze_stability_v2(construct: dict, *, environment: dict | None=None, generations: int=100, population: int=5000, replicates: int=32, seed: int=42) -> dict:
    sim=stochastic_drift_v2(construct,environment=environment,generations=generations,population=population,replicates=replicates,seed=seed); opt=optimize_stability_v2(construct,environment,generations=generations); mol=sim["molecular_profile"]
    return {"simulation":sim,"molecular_profile":mol,"sequence_risk_map":mol["sequence_risk_map"],"interventions":opt,"mutation_risk_map":{"point":mol["mutation_rates"]["point"],"insertion":mol["mutation_rates"]["insertion"],"deletion":mol["mutation_rates"]["deletion"],"vulnerable_regions":mol["sequence_risk_map"]["vulnerable_regions"]},"recommended_strategy":opt["selected"],"validation_plan":["deep-sequence serial passages","measure copy number by ddPCR","assay aggregation and protein turnover","stress-test temperature pH and oxidation","quantify metabolite and cofactor decay"],"model_status":"mechanistic hermetic molecular and population stability; no production-lot claim"}

def enhancement_features_v2(result: dict) -> dict:
    """Compute exactly 50 full-stack molecular/environment/CNV diagnostics."""
    import numpy as np
    sim=result["simulation"]; mol=result["molecular_profile"]; seq=result["sequence_risk_map"]; tr=sim["trajectory"]; opt=result["interventions"]
    g=np.array([x["generation"] for x in tr]); f=np.array([x["functional_mean"] for x in tr]); cn=np.array([x["copy_number_mean"] for x in tr]); cmin=np.array([x["copy_number_min"] for x in tr]); cmax=np.array([x["copy_number_max"] for x in tr]); ext=np.array([x["extinct"] for x in tr]); terminal=np.array(sim["terminal_functional"]); terminal_cn=np.array(sim["terminal_copy_number"]); regions=seq["regions"]; risks=np.array([x["risk"] for x in regions]); rates=mol["mutation_rates"]; env=mol["environment"]; protein=mol["protein"]; bio=mol["biochemical"]; rank=opt["ranking"]; scores=np.array([x["score"] for x in rank])
    out={"sequence_length":seq["sequence_length"],"risk_window_count":len(regions),"vulnerable_region_count":len(seq["vulnerable_regions"]),"sequence_risk_max":seq["maximum_risk"],"sequence_risk_mean":seq["mean_risk"],"sequence_risk_range":float(np.ptp(risks)),"maximum_gc_skew":max(abs(x["gc_skew"]) for x in regions),"maximum_homopolymer":max(x["max_homopolymer"] for x in regions),"maximum_repeat_score":max(x["repeat_score"] for x in regions),"maximum_hairpin_stem_bp":max(x["hairpin_stem_bp"] for x in regions),"point_mutation_rate":rates["point"],"insertion_rate":rates["insertion"],"deletion_rate":rates["deletion"],"total_mutation_rate":sum(rates.values()),"cnv_rate_per_generation":mol["cnv_rate_per_generation"],"temperature_C":env["temperature_C"],"pH":env["pH"],"oxidative_stress":env["oxidative_stress"],"environmental_stress_index":mol["environmental_stress_index"],"folding_energy_proxy":protein["folding_energy_proxy"],"aggregation_probability":protein["aggregation_probability"],"protein_degradation_rate_per_h":protein["degradation_rate_per_h"],"metabolite_24h_survival":bio["metabolite_24h_survival"],"cofactor_24h_survival":bio["cofactor_24h_survival"],"generation_count":int(g[-1]),"timepoint_count":len(g),"initial_functional_mean":float(f[0]),"terminal_functional_mean":float(f[-1]),"functional_change":float(f[-1]-f[0]),"functional_auc":float(np.trapz(f,g)),"functional_decline_per_generation":float((f[0]-f[-1])/max(g[-1],1)),"terminal_distribution_min":float(terminal.min()),"terminal_distribution_max":float(terminal.max()),"terminal_distribution_range":float(np.ptp(terminal)),"terminal_survival_probability":float(np.mean(terminal>.5)),"terminal_extinction_probability":float(np.mean(terminal==0)),"initial_copy_number_mean":float(cn[0]),"terminal_copy_number_mean":float(cn[-1]),"copy_number_mean_change":float(cn[-1]-cn[0]),"terminal_copy_number_min":float(cmin[-1]),"terminal_copy_number_max":float(cmax[-1]),"terminal_copy_number_range":float(cmax[-1]-cmin[-1]),"terminal_copy_number_distribution_range":float(np.ptp(terminal_cn)),"terminal_extinct_replicates":int(ext[-1]),"intervention_count":len(rank),"selected_intervention_score":rank[0]["score"],"selected_terminal_functional":rank[0]["terminal_functional"],"intervention_score_range":float(np.ptp(scores)),"intervention_score_margin":float(scores[0]-scores[1]),"environment_adjusted_stability":float(f[-1]*(1-protein["aggregation_probability"])*bio["metabolite_24h_survival"]*bio["cofactor_24h_survival"])}
    assert len(out)==50
    return out


# Canonical full-stack API. This deliberately overrides the earlier v1 wrapper.
def analyze_stability(construct: dict, *, environment: dict | None=None, generations: int=100,
                      population: int=5000, replicates: int=32, seed: int=42) -> dict:
    """Run full sequence, molecular, biochemical, environmental, CNV and population stability."""
    result=analyze_stability_v2(construct,environment=environment,generations=generations,population=population,replicates=replicates,seed=seed)
    result["diagnostics"]=enhancement_features_v2(result); result["diagnostic_count"]=50
    return result

# Canonical compatibility-preserving full-stack wrapper (v4).
def analyze_stability(construct: dict, *, environment: dict | None=None, generations: int=100,
                      population: int=5000, replicates: int=32, seed: int=42) -> dict:
    result=analyze_stability_v2(construct,environment=environment,generations=generations,population=population,replicates=replicates,seed=seed)
    result["diagnostics"]=enhancement_features_v2(result); result["diagnostic_count"]=50
    c=result["simulation"]["construct"]
    result["failure_modes"]=_failure_modes(c["mode"],c["burden"],c["toxic"])
    result["validation_plan"]=["deep-sequence serial passages","measure copy number by ddPCR","assay protein folding and aggregation","stress-test temperature pH oxidation and biochemical decay"]
    result["model_status"]="mechanistic hermetic full-stack stability model; no production-lot prediction"
    result["simulation"]["model_status"]="mechanistic hermetic Wright-Fisher/CNV/environment model; no production-lot prediction"
    return result
