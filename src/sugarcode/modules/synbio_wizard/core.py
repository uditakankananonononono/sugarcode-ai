"""Constraint-aware synthetic-biology design compiler.

Models are transparent mechanistic/heuristic surrogates with no trained model
and are not clinically validated. Outputs support design review, not physical
execution. Concentration is mM, flux mmol/gDW/h, time hours, and energy kJ/mol.
"""
from __future__ import annotations
import json, math, random
from xml.etree.ElementTree import Element, SubElement, tostring
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import linprog

PRODUCTS={
 "insulin":{"pathway":["proinsulin expression","proteolytic maturation","secretion"],"product_type":"protein","atp_cost":"high","difficulty":.6},
 "artemisinin_precursor":{"pathway":["MVA pathway","FPP synthesis","amorphadiene synthase","P450 oxidation"],"product_type":"metabolite","atp_cost":"very high","difficulty":.85},
 "vanillin":{"pathway":["tyrosine synthesis","deamination","hydroxylation","methylation"],"product_type":"metabolite","atp_cost":"medium","difficulty":.4},
 "spider_silk":{"pathway":["repetitive protein expression","secretion/spinning"],"product_type":"protein","atp_cost":"very high","difficulty":.75},
 "butanol":{"pathway":["acetyl-CoA","acetoacetyl-CoA","butyryl-CoA","butanol"],"product_type":"metabolite","atp_cost":"medium","difficulty":.45}}
CHASSIS={"E_coli":{"protein":.9,"metabolite":.8,"atp_budget":.7,"ease":.95,"gc_target":.51,"temperature_c":37},"S_cerevisiae":{"protein":.8,"metabolite":.9,"atp_budget":.8,"ease":.85,"gc_target":.38,"temperature_c":30},"CHO":{"protein":.95,"metabolite":.3,"atp_budget":.9,"ease":.4,"gc_target":.42,"temperature_c":37},"B_subtilis":{"protein":.75,"metabolite":.7,"atp_budget":.6,"ease":.8,"gc_target":.44,"temperature_c":37}}
__all__=["PRODUCTS","CHASSIS","run_wizard","parse_goal","score_chassis","codon_metrics","rbs_thermodynamics","promoter_kinetics","binding_occupancy","michaelis_menten","enzyme_capacity","flux_balance","resource_burden","deterministic_expression","gillespie_expression","logic_circuit","scan_guides","variant_effect","mutation_propagation","evolutionary_stability","uncertainty_distribution","compare_strategies","suggest_experiments","assembly_recommendation","sbml_export","knowledge_graph","ingest_experimental_feedback","feedback_posterior","wizard_diagnostics","compile_project","docking_surrogate","environment_response","plasmid_architecture"]

def _unit(x,name):
 x=float(x)
 if not 0<=x<=1: raise ValueError(f"{name} must be in [0, 1]")
 return x

def parse_goal(goal):
 if not isinstance(goal,str) or not goal.strip(): raise ValueError("goal must be a non-empty string")
 key=goal.strip().lower().replace(" ","_")
 if key in PRODUCTS: return {"catalog_key":key,"objective":"produce","product":key,"constraints":{}}
 words=key.split('_'); matched=next((p for p in PRODUCTS if p in key),None)
 if not matched: raise KeyError(f"goal {goal!r} unknown; catalog: {sorted(PRODUCTS)}")
 return {"catalog_key":matched,"objective":"produce","product":matched,"constraints":{"source_text":goal}}

def score_chassis(product,weights=None):
 spec=PRODUCTS[product]; weights=weights or {"product_fit":.4,"atp":.25,"ease":.2,"difficulty":.15}
 ranked=[]
 for name,p in CHASSIS.items():
  score=weights["product_fit"]*p[spec["product_type"]]+weights["atp"]*p["atp_budget"]+weights["ease"]*p["ease"]-weights["difficulty"]*spec["difficulty"]
  ranked.append({"chassis":name,"score":round(score,4),"components":{"product_fit":p[spec["product_type"]],"atp_budget":p["atp_budget"],"ease":p["ease"],"difficulty":spec["difficulty"]}})
 return sorted(ranked,key=lambda x:(-x["score"],x["chassis"]))

def codon_metrics(dna,chassis="E_coli"):
 s=''.join(x for x in dna.upper() if x in 'ACGT')
 if len(s)<3 or len(s)%3: raise ValueError("coding DNA must be non-empty and divisible by 3")
 gc=(s.count('G')+s.count('C'))/len(s); codons=[s[i:i+3] for i in range(0,len(s),3)]; target=CHASSIS[chassis]["gc_target"]
 cai=max(.05,1-abs(gc-target)*1.7)*(len(set(codons))/min(61,len(codons)))**.15
 windows=[(w.count('G')+w.count('C'))/len(w) for i in range(0,len(s),30) if (w:=s[i:i+30])]
 return {"length_nt":len(s),"gc_fraction":gc,"gc_window_min":min(windows),"gc_window_max":max(windows),"cai_proxy":cai,"codon_diversity":len(set(codons))/len(codons),"internal_stop_count":sum(c in ('TAA','TAG','TGA') for c in codons[:-1])}

def rbs_thermodynamics(sequence,temperature_c=37):
 s=sequence.upper().replace('T','U'); pairs=sum(s[i:i+2] in ('GC','CG') for i in range(len(s)-1)); au=sum(s[i:i+2] in ('AU','UA') for i in range(len(s)-1)); dg=-2.4*pairs-1.1*au+3.4
 rt=.001987*(temperature_c+273.15); accessibility=1/(1+math.exp(-dg/rt))
 return {"delta_g_kcal_mol":dg,"accessibility":accessibility,"predicted_relative_initiation":accessibility*math.exp(-abs(len(s)-20)/30)}

def promoter_kinetics(regulator,kd=.5,hill=2,vmax=1,basal=.01,repressor=False):
 if min(regulator,kd,hill,vmax)<0 or kd==0 or hill==0: raise ValueError("kinetic values must be non-negative; kd/hill positive")
 occ=regulator**hill/(kd**hill+regulator**hill); regulated=1-occ if repressor else occ
 return {"occupancy":occ,"transcription_rate_reu_h":basal+vmax*regulated}

def binding_occupancy(ligand,kd,competitor=0,competitor_kd=1):
 if min(ligand,competitor)<0 or min(kd,competitor_kd)<=0: raise ValueError("concentrations non-negative and Kd positive")
 return (ligand/kd)/(1+ligand/kd+competitor/competitor_kd)

def michaelis_menten(substrate,vmax,km,inhibitor=0,ki=1):
 if min(substrate,vmax,inhibitor)<0 or min(km,ki)<=0: raise ValueError("invalid Michaelis-Menten values")
 return vmax*substrate/(km*(1+inhibitor/ki)+substrate)

def enzyme_capacity(kcat_per_s,enzyme_uM,km_mM,substrate_mM):
 if min(kcat_per_s,enzyme_uM,km_mM,substrate_mM)<0 or km_mM==0: raise ValueError("enzyme parameters invalid")
 return michaelis_menten(substrate_mM,kcat_per_s*enzyme_uM*3.6,km_mM)

def flux_balance(pathway,uptake_limit=10,atp_limit=20,redox_limit=12):
 """Linear-program pathway flux under precursor, ATP and redox constraints."""
 n=len(pathway)
 if n<1 or min(uptake_limit,atp_limit,redox_limit)<0: raise ValueError("pathway non-empty and limits non-negative required")
 # Serial pathway: each downstream flux cannot exceed its precursor flux.
 A=[]; b=[]
 for i in range(n-1):
  row=np.zeros(n); row[i+1]=1; row[i]=-1; A.append(row); b.append(0)
 A.extend([np.ones(n),np.arange(1,n+1)*.5]); b.extend([atp_limit,redox_limit])
 bounds=[(0,uptake_limit)]+[(0,None)]*(n-1); c=np.zeros(n); c[-1]=-1
 result=linprog(c,A_ub=np.array(A),b_ub=np.array(b),bounds=bounds,method='highs')
 if not result.success: raise ValueError("pathway constraints are infeasible")
 return {"steps":list(pathway),"fluxes_mmol_gdw_h":{name:float(v) for name,v in zip(pathway,result.x)},"product_flux_mmol_gdw_h":float(result.x[-1]),"atp_use":float(result.x.sum()),"redox_use":float(np.arange(1,n+1)@result.x*.5),"solver":"scipy-highs linear program"}

def resource_burden(copy_number,promoter_strength,protein_length_aa,host_capacity=1e6):
 if min(copy_number,promoter_strength,protein_length_aa)<0 or host_capacity<=0: raise ValueError("burden inputs non-negative and capacity positive")
 atp=copy_number*promoter_strength*protein_length_aa*4; fraction=min(1,atp/host_capacity)
 return {"atp_demand":atp,"host_capacity":host_capacity,"fraction":fraction,"class":"low" if fraction<.2 else "moderate" if fraction<.5 else "high"}

def deterministic_expression(hours=24,transcription=1,translation=2,mrna_decay=.5,protein_decay=.1):
 if min(hours,transcription,translation,mrna_decay,protein_decay)<=0: raise ValueError("expression parameters must be positive")
 t=np.linspace(0,hours,100)
 def rhs(_t,y): return [transcription-mrna_decay*y[0],translation*y[0]-protein_decay*y[1]]
 sol=solve_ivp(rhs,(0,hours),[0,0],t_eval=t,rtol=1e-8,atol=1e-10)
 return {"time_hours":sol.t.tolist(),"mrna":sol.y[0].tolist(),"protein":sol.y[1].tolist(),"steady_protein":translation*transcription/(mrna_decay*protein_decay)}

def gillespie_expression(hours=24,transcription=1,translation=2,mrna_decay=.5,protein_decay=.1,seed=0):
 if min(hours,transcription,translation,mrna_decay,protein_decay)<=0: raise ValueError("SSA parameters positive required")
 rng=np.random.default_rng(seed); t=0.; m=p=0; events=[]; truncated=False
 while t<hours:
  if len(events)>=200000: truncated=True; break
  rates=np.array([transcription,translation*m,mrna_decay*m,protein_decay*p]); total=rates.sum(); t+=rng.exponential(1/total)
  if t>hours: break
  event=int(rng.choice(4,p=rates/total)); m+=1 if event==0 else -1 if event==2 else 0; p+=1 if event==1 else -1 if event==3 else 0; events.append((t,m,p))
 return {"hours":hours,"simulated_hours":round(t,4),"truncated":truncated,"seed":seed,"event_count":len(events),"final_mrna":m,"final_protein":p,"events":events}

def logic_circuit(operator,inputs):
 vals=[bool(x) for x in inputs]; op=operator.upper()
 if op=='AND': out=all(vals)
 elif op=='OR': out=any(vals)
 elif op=='NOT' and len(vals)==1: out=not vals[0]
 else: raise ValueError("operator must be AND/OR, or unary NOT")
 return {"operator":op,"inputs":vals,"output":out,"implementation":"activator coincidence" if op=='AND' else "parallel activation" if op=='OR' else "transcriptional repression"}

def scan_guides(sequence,pams=('NGG','NAG')):
 s=''.join(x for x in sequence.upper() if x in 'ACGT'); guides=[]
 def match(x,p): return len(x)==len(p) and all(b==q or q=='N' for b,q in zip(x,p))
 for pam in pams:
  for i in range(20,len(s)-len(pam)+1):
   if match(s[i:i+len(pam)],pam):
    g=s[i-20:i]; gc=(g.count('G')+g.count('C'))/20; seed=g[-12:]
    guides.append({"guide":g,"pam":s[i:i+len(pam)],"pam_pattern":pam,"start":i-20,"gc":gc,"gc_optimal":.4<=gc<=.6,"seed_complexity":len(set(seed))/4,"off_target_proxy":(1-abs(gc-.5))*len(set(seed))/4})
 return sorted(guides,key=lambda x:(not x['gc_optimal'],-x['off_target_proxy'],x['start']))

def variant_effect(ref_codon,alt_codon,conservation=.5,active_site=False):
 code={"GCT":"A","GCC":"A","GCA":"A","GCG":"A","TGG":"W","TGA":"*","TAA":"*","TAG":"*","GAA":"E","GAG":"E","GAC":"D","GAT":"D","AAA":"K","AAG":"K","ATG":"M"}
 ref=code.get(ref_codon.upper()); alt=code.get(alt_codon.upper())
 if ref is None or alt is None: raise ValueError("codon not in the translation table (was: silently mapped to X, so invalid codons scored as synonymous); valid: "+str(sorted(code)))
 cons=_unit(conservation,'conservation'); stop=alt=='*'; missense=ref!=alt and not stop
 sift=max(0,1-cons-(.3 if active_site else 0)); poly=min(1,.2+.6*cons+(.2 if active_site else 0)+(.3 if stop else 0))
 return {"ref_aa":ref,"alt_aa":alt,"class":"stop_gain" if stop else "missense" if missense else "synonymous","sift_proxy":sift,"polyphen_proxy":poly,"deleterious_probability":max(1-sift,poly)}

def mutation_propagation(ref_codon,alt_codon,baseline_flux=1,growth_rate=.5,active_site=False):
 v=variant_effect(ref_codon,alt_codon,active_site=active_site); ddg=3*v['deleterious_probability']; retained=math.exp(-ddg/2); flux=baseline_flux*retained; growth=growth_rate*(.4+.6*retained)
 return {"variant":v,"ddg_kcal_mol":ddg,"folded_fraction_retained":retained,"pathway_flux":flux,"growth_rate_h":growth,"phenotype_change_fraction":1-growth/growth_rate}

def evolutionary_stability(generations=100,mutation_rate=1e-6,burden=.1,selection=.02):
 if generations<0 or min(mutation_rate,burden,selection)<0: raise ValueError("evolution inputs non-negative required")
 functional=(1-mutation_rate)**generations*math.exp(-max(0,burden-selection)*generations)
 return {"generations":generations,"functional_fraction":functional,"loss_probability":1-functional,"effective_selection":selection-burden,"half_life_generations":math.log(2)/max(mutation_rate+max(0,burden-selection),1e-12)}

def docking_surrogate(contact_count,hydrogen_bonds,charge_penalty=0,flexibility=.5):
 if min(contact_count,hydrogen_bonds,charge_penalty)<0: raise ValueError("docking inputs non-negative required")
 dg=-.25*contact_count-1.2*hydrogen_bonds+.7*charge_penalty+2*_unit(flexibility,'flexibility')
 return {"delta_g_kcal_mol":dg,"relative_affinity":math.exp(-dg/(.001987*310.15)),"limitation":"Rigid-contact surrogate omits explicit solvent and conformational ensembles."}

def uncertainty_distribution(mean,model_cv=.15,data_n=20,seed=0,samples=1000):
 if mean<0 or model_cv<0 or data_n<1 or samples<2: raise ValueError("uncertainty inputs invalid")
 rng=np.random.default_rng(seed); sigma=max(1e-12,mean*model_cv*math.sqrt(1+1/data_n)); vals=np.maximum(0,rng.normal(mean,sigma,samples))
 return {"mean":float(vals.mean()),"std":float(vals.std()),"ci90":[float(np.quantile(vals,.05)),float(np.quantile(vals,.95))],"samples":samples,"seed":seed,"epistemic_fraction":1/math.sqrt(data_n)}

def compare_strategies(strategies):
 if not strategies: raise ValueError("at least one strategy required")
 out=[]
 for s in strategies:
  efficiency=_unit(s['efficiency'],'efficiency'); robustness=_unit(s['robustness'],'robustness'); risk=_unit(s['risk'],'risk'); score=.45*efficiency+.35*robustness-.2*risk
  out.append({**s,"tradeoff_score":score,"dominant_tradeoff":max({'efficiency':efficiency,'robustness':robustness,'risk_avoidance':1-risk},key={'efficiency':efficiency,'robustness':robustness,'risk_avoidance':1-risk}.get)})
 return sorted(out,key=lambda x:-x['tradeoff_score'])

def suggest_experiments(uncertainties,budget=3):
 mapping={"flux":"13C flux profiling or targeted metabolite time course","expression":"promoter/RBS strength library with expression readout","stability":"serial-passaging retention assay","structure":"mutational scan around predicted structural contacts","repair":"amplicon sequencing of repair outcomes","burden":"growth and resource-reporter curve across copy numbers"}
 ranked=sorted(uncertainties,key=lambda x:-x.get('uncertainty',0))[:budget]
 return [{"target":x['name'],"uncertainty":x.get('uncertainty',0),"experiment":mapping.get(x.get('domain'),"targeted factorial perturbation with orthogonal readout"),"expected_information_gain":x.get('uncertainty',0)*x.get('decision_sensitivity',1)} for x in ranked]

def assembly_recommendation(parts):
 if parts<1: raise ValueError("parts must be >=1")
 return {"method":"Golden Gate" if parts<=10 else "Gibson","parts":parts,"standard":"MoClo level-1 transcription units" if parts<=10 else "overlap-assembled multi-part construct","design_status":"Architecture only; institutional review and validated procedures required."}

def plasmid_architecture(genes,chassis='E_coli'):
 if not genes: raise ValueError("at least one gene required")
 return {"backbone":"low-copy bacterial" if chassis in ('E_coli','B_subtilis') else "yeast shuttle" if chassis=='S_cerevisiae' else "mammalian episomal","modules":[{"position":i+1,"promoter":"inducible","gene":g,"terminator":"host-compatible"} for i,g in enumerate(genes)],"assembly":assembly_recommendation(len(genes)*3)}

def sbml_export(pathway,fluxes=None):
 root=Element('sbml',{'level':'3','version':'2'}); model=SubElement(root,'model',{'id':'synbio_wizard_model'}); species=SubElement(model,'listOfSpecies')
 for i,name in enumerate(['precursor']+list(pathway)): SubElement(species,'species',{'id':f'S{i}','name':name,'compartment':'cell'})
 reactions=SubElement(model,'listOfReactions')
 for i,name in enumerate(pathway):
  r=SubElement(reactions,'reaction',{'id':f'R{i+1}','name':name,'reversible':'false'}); r.set('estimatedFlux',str((fluxes or {}).get(name,0)))
 return tostring(root,encoding='unicode')

def knowledge_graph(product):
 spec=PRODUCTS[product]; nodes=[{"id":product,"type":"product"}]+[{"id":step,"type":"pathway_step"} for step in spec['pathway']]
 edges=[]
 for i,step in enumerate(spec['pathway']): edges.append({"source":product if i==0 else spec['pathway'][i-1],"target":step,"relation":"requires" if i==0 else "precedes","evidence":"catalog design model"})
 return {"nodes":nodes,"edges":edges,"source_provenance":{"catalog":"embedded curated design examples","live_sources":False}}

def feedback_posterior(successes,total,prior_alpha=1,prior_beta=1):
 if not 0<=successes<=total or min(prior_alpha,prior_beta)<=0: raise ValueError("feedback counts/prior invalid")
 a=prior_alpha+successes; b=prior_beta+total-successes; mean=a/(a+b); var=a*b/((a+b)**2*(a+b+1)); return {"alpha":a,"beta":b,"mean":mean,"std":math.sqrt(var)}

def ingest_experimental_feedback(records,previous=None):
 state=dict(previous or {})
 for r in records:
  name=str(r['design']); old=state.get(name,{'alpha':1,'beta':1}); state[name]=feedback_posterior(int(r['successes']),int(r['total']),old['alpha'],old['beta'])
 return {"posterior":state,"records_ingested":len(records),"normalization":"count-level Beta-Binomial update"}

def environment_response(base_rate,temperature_c=37,ph=7,nutrient=.8):
 nutrient=_unit(nutrient,'nutrient'); q10=2**((temperature_c-37)/10); ph_factor=math.exp(-((ph-7)/1.5)**2); return {"relative_rate":base_rate*q10*ph_factor*nutrient,"temperature_factor":q10,"ph_factor":ph_factor,"nutrient_factor":nutrient}

def wizard_diagnostics(product,chassis=None):
 spec=PRODUCTS[product]; ranking=score_chassis(product); chassis=chassis or ranking[0]['chassis']; props=CHASSIS[chassis]; n=len(spec['pathway']); fb=flux_balance(spec['pathway']); stability=evolutionary_stability(burden=spec['difficulty']*.1)
 d={"pathway_step_count":float(n),"difficulty":float(spec['difficulty']),"chassis_product_fit":float(props[spec['product_type']]),"chassis_atp_budget":float(props['atp_budget']),"chassis_ease":float(props['ease']),"chassis_gc_target":float(props['gc_target']),"chassis_temperature_c":float(props['temperature_c']),"top_chassis_score":float(ranking[0]['score']),"top_vs_second_margin":float(ranking[0]['score']-ranking[1]['score']),"parts_estimate":float(n+2),"product_flux":float(fb['product_flux_mmol_gdw_h']),"atp_use":float(fb['atp_use']),"redox_use":float(fb['redox_use']),"stability_functional_fraction":float(stability['functional_fraction']),"stability_half_life_generations":float(stability['half_life_generations'])}
 costs={'medium':.5,'high':.75,'very high':1}; d['atp_cost_class']=costs[spec['atp_cost']]; d['protein_product']=float(spec['product_type']=='protein'); d['metabolite_product']=float(spec['product_type']=='metabolite'); d['assembly_golden_gate']=float(n+2<=10); d['uncertainty_prior']=.1+.4*spec['difficulty']
 for i,name in enumerate(CHASSIS): d[f'chassis_score.{name}']=float(next(x['score'] for x in ranking if x['chassis']==name))
 for i,step in enumerate(spec['pathway'][:8]): d[f'step_{i+1}.relative_flux']=float(fb['fluxes_mmol_gdw_h'][step]/max(fb['product_flux_mmol_gdw_h'],1e-12))
 return d

def compile_project(goal,seed=42,parts_max=8):
 parsed=parse_goal(goal); product=parsed['product']; spec=PRODUCTS[product]; ranking=score_chassis(product); selected=ranking[0]; pathway=flux_balance(spec['pathway']); assembly=assembly_recommendation(len(spec['pathway'])+2); uncertainty=uncertainty_distribution(max(.05,pathway['product_flux_mmol_gdw_h']/10),.15+.2*spec['difficulty'],20,seed)
 unknown=[{"name":"pathway flux","domain":"flux","uncertainty":uncertainty['epistemic_fraction'],"decision_sensitivity":spec['difficulty']},{"name":"construct persistence","domain":"stability","uncertainty":.1+spec['difficulty']*.3,"decision_sensitivity":.8},{"name":"host burden","domain":"burden","uncertainty":spec['difficulty']*.25,"decision_sensitivity":.7}]
 return {"goal":parsed,"pathway":pathway,"chassis_ranking":ranking,"selected_chassis":selected,"assembly":assembly,"plasmid":plasmid_architecture(spec['pathway'],selected['chassis']),"yield_distribution":uncertainty,"evolution":evolutionary_stability(burden=.1*spec['difficulty']),"knowledge_graph":knowledge_graph(product),"sbml":sbml_export(spec['pathway'],pathway['fluxes_mmol_gdw_h']),"diagnostics":wizard_diagnostics(product,selected['chassis']),"uncertainties":unknown,"suggested_experiments":suggest_experiments(unknown),"model_status":"Transparent mechanistic/heuristic models; no trained model and not clinically validated."}

def run_wizard(goal,parts_max=8,seed=42):
 """Backward-compatible guided design result backed by compiler analyses."""
 project=compile_project(goal,seed,parts_max); product=project['goal']['product']; spec=PRODUCTS[product]; rng=random.Random(seed); steps=spec['pathway']; n_parts=len(steps)+2
 if parts_max<1: raise ValueError("parts_max must be >= 1")
 base=max(.05,.9-spec['difficulty']-.05*(n_parts-4)); runs=sorted(max(0,base*(1+rng.gauss(0,.25))) for _ in range(200)); mean=round(sum(runs)/len(runs),3); ci=(round(runs[5],3),round(runs[195],3)); chassis=project['selected_chassis']; feasibility=round(min(1,mean*chassis['score']/.5),2)
 uncertainties=[]
 if spec['atp_cost'] in ('high','very high'): uncertainties.append('ATP/redox burden may cap titer - evaluate pathway flux constraints before build')
 if spec['difficulty']>.6: uncertainties.append('multi-enzyme balancing unresolved - promoter library recommended')
 return {"goal":product,"steps":{"1_goal":spec,"2_pathway":steps,"3_chassis_ranking":[{"chassis":x['chassis'],"score":round(x['score'],3)} for x in project['chassis_ranking']],"4_selected_chassis":{"chassis":chassis['chassis'],"score":round(chassis['score'],3)},"5_assembly":{"method":project['assembly']['method'],"parts":n_parts,"overhangs":[f'O{i}' for i in range(1,n_parts)] if project['assembly']['method']=='Golden Gate' else None},"6_yield_simulation":{"mean_titer_fraction":mean,"90pct_CI":ci,"n_monte_carlo":200}},"feasibility_score":feasibility,"verdict":"go" if feasibility>.45 else "redesign needed","uncertainties":uncertainties,"suggested_experiments":["promoter strength library on rate-limiting step","chassis head-to-head at small scale","metabolite assay at 24/48/72 h"],"compiler":project}
