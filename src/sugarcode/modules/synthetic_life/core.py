"""Synthetic Life industrial minimal-genome and bioprocess compiler.

Models are explicit mechanistic/optimization models with no trained model and
not clinically validated. Outputs are computational design evidence, not wet-
lab operating procedures. Flux units are mmol/gDW/h and time is hours.
"""
from __future__ import annotations
import math, random
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import linprog
from ..virtual_cell.core import MetabolicModel,demo_model,gene_knockout,fba
CATEGORY_ESSENTIALITY={"replication":.85,"transcription":.8,"translation":.9,"glycolysis":.6,"membrane_transport":.65,"cell_envelope":.55,"cofactor_biosynthesis":.5,"lipid_metabolism":.45,"nucleotide_metabolism":.55,"stress_response":.2,"motility":.05,"secondary_metabolism":.05,"unknown":.3}
__all__=["CATEGORY_ESSENTIALITY","essentiality_scan","design_minimal_genome","gene_evidence_score","optimize_minimal_genome","validate_genome_design","flux_optimize","dynamic_fba","cofactor_balance","overflow_metabolism","monod_rate","oxygen_transfer","fermentation_simulate","stress_response","resilience_design","promoter_copy_optimize","integration_site_score","dynamic_control","stochastic_control","circuit_burden","ale_trajectory","beneficial_mutations","compare_genomes","functional_gap_analysis","regulatory_compatibility","modular_chassis","production_module","genome_diagnostics","compile_synthetic_life","process_scale_risk"]

def _unit(x,name):
 x=float(x)
 if not 0<=x<=1: raise ValueError(f"{name} must be in [0, 1]")
 return x

def _default_catalog():
 rng=random.Random(7); cats=list(CATEGORY_ESSENTIALITY); weights=[8,8,10,12,10,8,6,8,8,6,4,4,8]
 return [{"name":f"MG_{i+1:03d}","category":rng.choices(cats,weights)[0],"size_bp":rng.randint(300,3000)} for i in range(450)]

def _count_by(genes,key):
 out={}
 for gene in genes: out[gene[key]]=out.get(gene[key],0)+1
 return out

def essentiality_scan(model=None):
 model=model or demo_model(); results=[]
 for reaction in model.reactions:
  ko=gene_knockout(model,reaction); results.append({"reaction":reaction,"growth_ratio":ko["growth_ratio"],"class":ko["lethality"]})
 essential=[r for r in results if r['class']=='lethal']
 return {"model_reactions":len(results),"scan":results,"essential_reactions":[r['reaction'] for r in essential],"essential_fraction":round(len(essential)/len(results),3)}

def gene_evidence_score(gene):
 prior=CATEGORY_ESSENTIALITY.get(gene.get('category','unknown'),.3); crispr=_unit(gene.get('crispr_essentiality',prior),'crispr_essentiality'); transposon=_unit(gene.get('transposon_essentiality',prior),'transposon_essentiality'); conservation=_unit(gene.get('conservation',prior),'conservation'); model=_unit(gene.get('model_essentiality',prior),'model_essentiality')
 evidence=.3*crispr+.25*transposon+.2*conservation+.25*model
 return {"prior":prior,"crispr":crispr,"transposon":transposon,"conservation":conservation,"whole_cell":model,"posterior_essentiality":evidence,"uncertainty":float(np.std([crispr,transposon,conservation,model]))}

def optimize_minimal_genome(genes,minimum_category_coverage=1,max_risk=.35):
 if not genes: raise ValueError("genes must not be empty")
 evidence={g['name']:gene_evidence_score(g) for g in genes}; required={g['name'] for g in genes if evidence[g['name']]['posterior_essentiality']>=1-max_risk}; categories={g['category'] for g in genes}
 for category in categories:
  candidates=sorted((g for g in genes if g['category']==category),key=lambda g:(-evidence[g['name']]['posterior_essentiality'],g['size_bp']))[:minimum_category_coverage]; required.update(g['name'] for g in candidates)
 kept=[g for g in genes if g['name'] in required]; dropped=[g for g in genes if g['name'] not in required]
 return {"kept":kept,"dropped":dropped,"objective_bp":sum(g.get('size_bp',1000) for g in kept),"constraints":{"max_deletion_risk":max_risk,"minimum_category_coverage":minimum_category_coverage},"evidence":evidence}

def validate_genome_design(design):
 kept=design['kept']; names=[g['name'] for g in kept]; category_counts=_count_by(kept,'category'); duplicate=len(names)!=len(set(names)); missing_core=[c for c in ('replication','transcription','translation') if category_counts.get(c,0)==0]
 return {"valid":not duplicate and not missing_core,"duplicate_gene_names":duplicate,"missing_core_categories":missing_core,"category_counts":category_counts,"genome_bp":sum(g.get('size_bp',1000) for g in kept)}

def design_minimal_genome(genes=None):
 genes=genes or _default_catalog(); scored=[]
 for g in genes:
  prior=CATEGORY_ESSENTIALITY.get(g['category'],.3); scored.append({**g,"essentiality_prior":prior,"keep":prior>=.45})
 kept=[g for g in scored if g['keep']]; dropped=[g for g in scored if not g['keep']]; original=sum(g.get('size_bp',1000) for g in genes); genome=sum(g.get('size_bp',1000) for g in kept)
 return {"input_genes":len(genes),"minimal_set_size":len(kept),"genome_size_bp":genome,"reduction_fraction":round(1-genome/original,3),"kept_by_category":_count_by(kept,'category'),"dropped_by_category":_count_by(dropped,'category'),"metabolic_support":essentiality_scan(),"chassis_protocol":["partition design into reviewable genomic segments","select a validated assembly strategy","verify genome integrity and phenotype with institutional controls"]}

def flux_optimize(model=None,product_reaction='BIOMASS',growth_floor=0,oxygen_limit=None,glucose_limit=None):
 model=model or demo_model(); c=np.zeros(len(model.reactions)); c[model.rxn_index(product_reaction)]=-1; bounds=list(zip(model.lb.copy(),model.ub.copy()))
 bounds=[list(x) for x in bounds]
 if glucose_limit is not None and 'GLC_UP' in model.reactions: bounds[model.rxn_index('GLC_UP')][1]=glucose_limit
 if oxygen_limit is not None and 'RESP' in model.reactions: bounds[model.rxn_index('RESP')][1]=oxygen_limit
 A=[]; b=[]
 if product_reaction!='BIOMASS' and 'BIOMASS' in model.reactions:
  row=np.zeros(len(model.reactions)); row[model.rxn_index('BIOMASS')]=-1; A.append(row); b.append(-growth_floor)
 result=linprog(c,A_eq=model.S,b_eq=np.zeros(len(model.metabolites)),A_ub=np.array(A) if A else None,b_ub=np.array(b) if b else None,bounds=[tuple(x) for x in bounds],method='highs')
 if not result.success: return {"status":"infeasible","objective":0,"fluxes":{r:0 for r in model.reactions}}
 return {"status":"optimal","objective":float(-result.fun),"product_reaction":product_reaction,"fluxes":{r:float(v) for r,v in zip(model.reactions,result.x)},"growth_floor":growth_floor}

def monod_rate(substrate,mu_max=.6,ks=.2,inhibition=0,ki=10):
 if min(substrate,mu_max,inhibition)<0 or min(ks,ki)<=0: raise ValueError("Monod parameters invalid")
 return mu_max*substrate/(ks+substrate)/(1+inhibition/ki)

def oxygen_transfer(kla_per_h,dissolved_o2,saturation_o2,biomass=1,our_per_biomass=2):
 if min(kla_per_h,dissolved_o2,saturation_o2,biomass,our_per_biomass)<0: raise ValueError("oxygen values non-negative required")
 otr=kla_per_h*max(0,saturation_o2-dissolved_o2); our=biomass*our_per_biomass
 return {"otr_mmol_l_h":otr,"our_mmol_l_h":our,"oxygen_excess":otr-our,"oxygen_limited":our>otr}

def dynamic_fba(model=None,hours=24,dt=.25,glucose0=50,biomass0=.1,oxygen_limit=10):
 model=model or demo_model()
 if min(hours,dt,glucose0,biomass0,oxygen_limit)<=0: raise ValueError("dFBA parameters must be positive")
 t=0.; glucose=glucose0; biomass=biomass0; trajectory=[]
 while t<=hours and glucose>1e-9:
  uptake=min(10,glucose/max(biomass*dt,.00001)); sol=flux_optimize(model,glucose_limit=uptake,oxygen_limit=oxygen_limit); mu=sol['objective']*.1; growth=biomass*(math.exp(mu*dt)-1); biomass+=growth; glucose=max(0,glucose-uptake*biomass*.01*dt); trajectory.append({"time_h":t,"biomass_gdw_l":biomass,"glucose_mM":glucose,"growth_rate_h":mu,"uptake_flux":uptake}); t+=dt
 return {"trajectory":trajectory,"final_biomass_gdw_l":biomass,"final_glucose_mM":glucose,"oxygen_limit":oxygen_limit}

def cofactor_balance(nadh_production,nadh_use,nadph_production,nadph_use):
 if min(nadh_production,nadh_use,nadph_production,nadph_use)<0: raise ValueError("cofactor fluxes non-negative required")
 return {"NADH_balance":nadh_production-nadh_use,"NADPH_balance":nadph_production-nadph_use,"redox_imbalance":abs(nadh_production-nadh_use)+abs(nadph_production-nadph_use),"transhydrogenase_direction":"NADH_to_NADPH" if nadh_production-nadh_use>nadph_production-nadph_use else "NADPH_to_NADH"}

def overflow_metabolism(carbon_uptake,respiratory_capacity,yield_coefficient=.5):
 if min(carbon_uptake,respiratory_capacity,yield_coefficient)<0: raise ValueError("overflow values non-negative required")
 overflow=max(0,carbon_uptake-respiratory_capacity); return {"respired_flux":min(carbon_uptake,respiratory_capacity),"overflow_flux":overflow,"acetate_flux":overflow*.8,"biomass_flux":min(carbon_uptake,respiratory_capacity)*yield_coefficient}

def fermentation_simulate(hours=48,substrate0=100,biomass0=.1,product_yield=.4,mu_max=.6,ks=.2,kla=50,temperature_c=30,ph=7):
 if min(hours,substrate0,biomass0,product_yield,mu_max,ks,kla)<=0: raise ValueError("fermentation inputs positive required")
 temp=math.exp(-((temperature_c-30)/10)**2); phf=math.exp(-((ph-7)/1.5)**2)
 def rhs(_t,y):
  x,s,p,o=y; mu=monod_rate(max(s,0),mu_max*temp*phf,ks,inhibition=p,ki=100); oxygen_factor=o/(.1+o); growth=mu*oxygen_factor*x; uptake=growth/.5; otr=kla*(.21-o); return [growth,-uptake,product_yield*uptake,otr-2*growth]
 t=np.linspace(0,hours,193); sol=solve_ivp(rhs,(0,hours),[biomass0,substrate0,0,.21],t_eval=t,rtol=1e-7,atol=1e-9); y=np.maximum(sol.y,0)
 return {"time_h":sol.t.tolist(),"biomass_gdw_l":y[0].tolist(),"substrate_mM":y[1].tolist(),"product_mM":y[2].tolist(),"oxygen_mM":y[3].tolist(),"final_product_mM":float(y[2,-1]),"final_biomass_gdw_l":float(y[0,-1])}

def stress_response(ph=7,temperature_c=30,osmolarity=.3,product_mM=0):
 ph_score=math.exp(-((ph-7)/1.5)**2); temp_score=math.exp(-((temperature_c-30)/12)**2); osmotic=math.exp(-max(0,osmolarity-.3)*2); product=1/(1+product_mM/100); viability=ph_score*temp_score*osmotic*product
 return {"ph_tolerance":ph_score,"temperature_tolerance":temp_score,"osmotic_tolerance":osmotic,"product_tolerance":product,"combined_viability":viability}

def resilience_design(stress):
 suggestions=[]
 if stress['temperature_tolerance']<.8: suggestions.append({"module":"heat-shock chaperone regulation","target":"temperature resilience"})
 if stress['osmotic_tolerance']<.8: suggestions.append({"module":"compatible-solute transport","target":"osmotic resilience"})
 if stress['product_tolerance']<.8: suggestions.append({"module":"membrane/export engineering","target":"product tolerance"})
 return {"modules":suggestions,"predicted_resilience_gain":min(.3,.08*len(suggestions)),"architecture_only":True}

def promoter_copy_optimize(target_expression,burden_limit=.3,promoters=(.1,.3,.6,1),copies=(1,2,4,8)):
 if target_expression<0 or not 0<burden_limit<=1: raise ValueError("target non-negative and burden_limit in (0,1]")
 options=[]
 for promoter in promoters:
  for copy in copies:
   expression=promoter*copy; burden=1-math.exp(-expression/10); error=abs(expression-target_expression); options.append({"promoter_strength":promoter,"copy_number":copy,"expression":expression,"burden":burden,"feasible":burden<=burden_limit,"objective":error+max(0,burden-burden_limit)*10})
 feasible=[x for x in options if x['feasible']]; ranked=sorted(feasible or options,key=lambda x:x['objective']); return {"recommendation":ranked[0],"options":ranked}

def integration_site_score(accessibility,essential_gene_distance_bp,repeat_fraction,growth_effect=0):
 accessibility=_unit(accessibility,'accessibility'); repeat_fraction=_unit(repeat_fraction,'repeat_fraction'); growth_effect=_unit(growth_effect,'growth_effect')
 distance_score=1-math.exp(-essential_gene_distance_bp/1000); score=.4*accessibility+.3*distance_score+.2*(1-repeat_fraction)+.1*(1-growth_effect)
 return {"score":score,"accessibility":accessibility,"distance_safety":distance_score,"repeat_safety":1-repeat_fraction,"growth_safety":1-growth_effect}

def dynamic_control(density,threshold=1,basal=.02,max_output=1,hill=4,feedback=.2):
 if min(density,threshold,basal,max_output,hill,feedback)<0 or threshold==0 or hill==0: raise ValueError("control values invalid")
 signal=density**hill/(threshold**hill+density**hill); output=(basal+max_output*signal)/(1+feedback*signal)
 return {"density":density,"quorum_signal":signal,"production_output":output,"phase":"production" if signal>.5 else "growth"}

def stochastic_control(hours=12,dt=.05,seed=0,transcription=.5,translation=1,degradation=.2):
 if min(hours,dt,transcription,translation,degradation)<=0: raise ValueError("stochastic values positive required")
 rng=np.random.default_rng(seed); protein=0.; series=[]
 for t in np.arange(0,hours+dt/2,dt):
  drift=transcription*translation-degradation*protein; noise=math.sqrt(max(transcription*translation+degradation*protein,0)); protein=max(0,protein+drift*dt+noise*math.sqrt(dt)*rng.normal()); series.append(float(protein))
 return {"time_h":np.arange(0,hours+dt/2,dt).tolist(),"protein":series,"seed":seed,"mean":float(np.mean(series)),"cv":float(np.std(series)/max(np.mean(series),1e-12))}

def circuit_burden(gates,expression_per_gate=.2,capacity=10):
 if gates<0 or min(expression_per_gate,capacity)<=0: raise ValueError("circuit burden inputs invalid")
 fraction=gates*expression_per_gate/capacity; return {"gate_count":gates,"demand":gates*expression_per_gate,"capacity":capacity,"fraction":fraction,"acceptable":fraction<.25}

def ale_trajectory(generations=500,initial_fitness=1,mutation_supply=.02,selection=.05,seed=0):
 if generations<1 or initial_fitness<=0 or min(mutation_supply,selection)<0: raise ValueError("ALE inputs invalid")
 rng=np.random.default_rng(seed); fitness=initial_fitness; history=[]
 for g in range(generations+1):
  if rng.random()<mutation_supply: fitness*=1+rng.exponential(selection)
  history.append(fitness)
 return {"generations":generations,"fitness":history,"final_fitness":fitness,"gain":fitness/initial_fitness-1,"seed":seed}

def beneficial_mutations(stress_targets,top_n=5):
 if not stress_targets: raise ValueError("stress_targets required")
 candidates=[]
 for target,severity in stress_targets.items():
  severity=_unit(severity,target); candidates.extend([{"target":target,"mechanism":"regulatory attenuation","predicted_selection":.04*severity},{"target":target,"mechanism":"transport or membrane adaptation","predicted_selection":.03*severity}])
 return sorted(candidates,key=lambda x:-x['predicted_selection'])[:top_n]

def compare_genomes(ancient,modern):
 a={g['name']:g for g in ancient}; m={g['name']:g for g in modern}; common=set(a)&set(m)
 return {"shared_genes":sorted(common),"ancient_only":sorted(set(a)-set(m)),"modern_only":sorted(set(m)-set(a)),"shared_fraction":len(common)/max(1,len(set(a)|set(m))),"category_shifts":{c:sum(g['category']==c for g in modern)-sum(g['category']==c for g in ancient) for c in set(g['category'] for g in ancient+modern)}}

def functional_gap_analysis(source_genes,host_genes):
 host_categories={g['category'] for g in host_genes}; missing=[g for g in source_genes if g['category'] not in host_categories]; return {"missing_functions":missing,"gap_count":len(missing),"compatibility":1-len(missing)/max(1,len(source_genes))}

def regulatory_compatibility(source_gc,host_gc,motif_overlap,epigenetic_match=.5):
 motif_overlap=_unit(motif_overlap,'motif_overlap'); epigenetic_match=_unit(epigenetic_match,'epigenetic_match'); score=.3*(1-min(1,abs(source_gc-host_gc)*2))+.4*motif_overlap+.3*epigenetic_match
 return {"score":score,"gc_compatibility":1-min(1,abs(source_gc-host_gc)*2),"motif_overlap":motif_overlap,"epigenetic_match":epigenetic_match}

def production_module(product,genes,control='quorum_switch'):
 if not genes: raise ValueError("production module requires genes")
 return {"product":product,"genes":list(genes),"control":control,"interfaces":{"input":"host precursor/cofactor pool","output":product,"status_signal":"density or metabolite sensor"},"portable":True}

def modular_chassis(minimal_genome,modules):
 names=[m['product'] for m in modules]
 if len(names)!=len(set(names)): raise ValueError("module products must be unique")
 return {"base_genome_gene_count":minimal_genome['minimal_set_size'],"plug_in_modules":modules,"module_count":len(modules),"interface_standard":"precursor/cofactor/status-signal contract","total_gene_count":minimal_genome['minimal_set_size']+sum(len(m['genes']) for m in modules)}

def process_scale_risk(volume_l,kla,heat_removal_kw,oxygen_demand):
 if min(volume_l,kla,heat_removal_kw,oxygen_demand)<=0: raise ValueError("scale inputs positive required")
 oxygen_capacity=kla*volume_l*.001; heat_capacity=heat_removal_kw/volume_l; return {"oxygen_capacity":oxygen_capacity,"oxygen_margin":oxygen_capacity-oxygen_demand,"heat_removal_kw_l":heat_capacity,"oxygen_risk":oxygen_demand>oxygen_capacity,"heat_risk":heat_capacity<.001,"overall_risk":max(0,oxygen_demand-oxygen_capacity)/oxygen_demand+(1 if heat_capacity<.001 else 0)}

def genome_diagnostics(genes,model=None):
 if not genes: raise ValueError("genes required")
 evid=[gene_evidence_score(g) for g in genes]; sizes=np.array([g.get('size_bp',1000) for g in genes],float); priors=np.array([x['posterior_essentiality'] for x in evid]); cats=[g.get('category','unknown') for g in genes]; scan=essentiality_scan(model)
 d={"gene_count":float(len(genes)),"genome_size_bp":float(sizes.sum()),"gene_size_mean_bp":float(sizes.mean()),"gene_size_std_bp":float(sizes.std()),"gene_size_min_bp":float(sizes.min()),"gene_size_max_bp":float(sizes.max()),"essentiality_mean":float(priors.mean()),"essentiality_std":float(priors.std()),"essentiality_min":float(priors.min()),"essentiality_max":float(priors.max()),"high_essentiality_fraction":float(np.mean(priors>=.65)),"low_essentiality_fraction":float(np.mean(priors<.3)),"category_count":float(len(set(cats))),"metabolic_essential_fraction":float(scan['essential_fraction']),"unknown_fraction":float(cats.count('unknown')/len(cats))}
 for cat in CATEGORY_ESSENTIALITY: d[f'category_fraction.{cat}']=cats.count(cat)/len(cats)
 return d

def compile_synthetic_life(genes=None,product='biomass',module_genes=None,seed=0):
 genes=genes or _default_catalog(); optimized=optimize_minimal_genome(genes); validation=validate_genome_design(optimized); legacy=design_minimal_genome(genes); module=production_module(product,module_genes or ['enzyme_A','enzyme_B']); chassis=modular_chassis(legacy,[module]); fermentation=fermentation_simulate(hours=12); stress=stress_response(product_mM=fermentation['final_product_mM']); diagnostics=genome_diagnostics(genes)
 return {"genome_optimization":optimized,"validation":validation,"legacy_minimal_design":legacy,"chassis":chassis,"metabolic_optimization":flux_optimize(),"dynamic_fba":dynamic_fba(hours=4),"cofactor":cofactor_balance(10,8,5,6),"control":dynamic_control(1.5),"stochastic_control":stochastic_control(hours=2,seed=seed),"fermentation":fermentation,"stress":stress,"resilience":resilience_design(stress),"integration_site":integration_site_score(.8,2000,.05),"evolution":ale_trajectory(generations=50,seed=seed),"diagnostics":diagnostics,"model_status":"Mechanistic/optimization models only; no trained model and not clinically validated.","design_status":"Computational architecture requiring expert and institutional review before physical work."}
