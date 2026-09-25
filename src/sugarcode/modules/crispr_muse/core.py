"""CRISPR Muse: adaptive, traceable genome-editing design.

Muse uses an explicit categorical policy and Bayesian feedback updates. It has
no trained CNN/transformer model and is not clinically validated. Scores are
mechanistic or named heuristic surrogates, never claims of measured editing.
All sequence inputs are DNA 5' to 3'; probabilities are fractions in [0, 1].
"""
from __future__ import annotations
import json, math
from dataclasses import dataclass
from typing import Dict, List
import numpy as np
from ...bio.sequence import clean_dna, gc_content, reverse_complement
from ..crispr_opt.core import score_on_target, score_off_targets, cfd_score

NUCLEASES = {
 "SpCas9":{"pam":"NGG","guide_length":20,"cut_offset":-3,"editor":"nuclease"},
 "SaCas9":{"pam":"NNGRRT","guide_length":21,"cut_offset":-3,"editor":"nuclease"},
 "Cas12a":{"pam":"TTTV","guide_length":23,"cut_offset":18,"editor":"nuclease","pam_side":"5p"},
 "CasX":{"pam":"TTCN","guide_length":20,"cut_offset":14,"editor":"nuclease","pam_side":"5p"},
 "xCas9":{"pam":"NG","guide_length":20,"cut_offset":-3,"editor":"nuclease"},
}
BASES="ACGT"
__all__=["NUCLEASES","MuseAgent","train_round","pam_matches","pam_compatibility","enumerate_configurations","rna_folding_score","chromatin_prior","microhomology_score","repair_outcomes","base_editing_window","prime_editing_design","reward_decomposition","simulate_digital_lab","bayesian_posterior","ingest_sequencing_feedback","multiplex_compatibility","rank_strategies","policy_entropy","guide_diagnostics","design_muse_strategy","export_simulation","delivery_efficiency","clonal_expansion","sequence_error_model","guide_similarity","edit_precision","functional_impact","continual_learning_report"]


def _guide(sequence, length=20):
 s=clean_dna(sequence)
 if "N" in s or len(s)!=length: raise ValueError(f"guide must contain exactly {length} unambiguous A/C/G/T bases; received length {len(s)}")
 return s

def _unit(value,name):
 value=float(value)
 if not 0<=value<=1: raise ValueError(f"{name} must be in [0, 1], got {value}")
 return value

def _softmax(x,axis=-1):
 x=np.asarray(x,float); z=np.exp(x-x.max(axis=axis,keepdims=True)); return z/z.sum(axis=axis,keepdims=True)

def _iupac_match(base,code):
 return base in {"N":"ACGT","R":"AG","Y":"CT","V":"ACG","T":"T","A":"A","C":"C","G":"G"}.get(code,code)

def pam_matches(sequence,pattern):
 """Return whether a concrete PAM matches an IUPAC PAM pattern."""
 s=clean_dna(sequence); p=pattern.upper()
 return len(s)==len(p) and all(_iupac_match(a,b) for a,b in zip(s,p))

def pam_compatibility(pam,nuclease=None):
 """Compatibility map for a concrete PAM; optional single nuclease."""
 names=[nuclease] if nuclease else list(NUCLEASES)
 if any(n not in NUCLEASES for n in names): raise ValueError("unknown nuclease; choose "+", ".join(NUCLEASES))
 return {n:pam_matches(pam,NUCLEASES[n]["pam"]) for n in names}

def guide_similarity(a,b):
 a=clean_dna(a); b=clean_dna(b)
 if len(a)!=len(b): raise ValueError("guide sequences must have equal length")
 return sum(x==y for x,y in zip(a,b))/len(a)

def rna_folding_score(guide,length=20):
 """RNA availability proxy: penalizes longest inverted repeat and poly-T."""
 g=_guide(guide,length); rc=reverse_complement(g); longest=0
 for shift in range(-16,17):
  run=0
  for i,b in enumerate(g):
   j=i+shift; run=run+1 if 0<=j<len(g) and b==rc[j] else 0; longest=max(longest,run)
 return max(0.0,1.0-longest/12.0-(0.25 if "TTTT" in g else 0.0))

def chromatin_prior(accessibility=0.5, distance_to_peak=0.0, decay_bp=500.0):
 accessibility=_unit(accessibility,"accessibility")
 if distance_to_peak<0 or decay_bp<=0: raise ValueError("distance must be non-negative and decay_bp positive")
 return accessibility*math.exp(-distance_to_peak/decay_bp)

def microhomology_score(context,max_arm=8):
 s=clean_dna(context)
 if len(s)<4: raise ValueError("repair context must be at least 4 nt")
 mid=len(s)//2; best=0
 for k in range(2,min(max_arm,mid,len(s)-mid)+1):
  if s[mid-k:mid]==s[mid:mid+k]: best=max(best,k)
 return best/max_arm

def repair_outcomes(context,chromatin=0.5,donor_similarity=0.0,cell_cycle_s=0.25):
 """Normalized NHEJ/MMEJ/HDR distribution from context and repair priors."""
 chromatin=_unit(chromatin,"chromatin"); donor_similarity=_unit(donor_similarity,"donor_similarity"); cell_cycle_s=_unit(cell_cycle_s,"cell_cycle_s")
 mh=microhomology_score(context); raw=np.array([1.1-.35*mh, .2+1.5*mh, .05+1.4*donor_similarity*cell_cycle_s])*max(.05,chromatin)
 raw=raw/raw.sum(); frameshift=min(1.0,raw[0]*2/3+raw[1]*.5)
 return {"NHEJ":float(raw[0]),"MMEJ":float(raw[1]),"HDR":float(raw[2]),"frameshift":float(frameshift),"microhomology":mh}

def base_editing_window(guide,editor="CBE",window=(4,8)):
 g=_guide(guide); start,end=window
 if editor not in ("CBE","ABE"): raise ValueError("editor must be CBE or ABE")
 if not 1<=start<=end<=len(g): raise ValueError("editing window must use 1-based coordinates inside guide")
 source="C" if editor=="CBE" else "A"; target="T" if editor=="CBE" else "G"
 return {"editor":editor,"window":list(window),"editable_positions":[i+1 for i,b in enumerate(g) if start<=i+1<=end and b==source],"conversion":source+">"+target}

def prime_editing_design(spacer,extension,primer_binding_length=13,rt_length=None):
 spacer=_guide(spacer); ext=clean_dna(extension)
 if not 8<=primer_binding_length<len(ext): raise ValueError("primer_binding_length must be >=8 and shorter than extension")
 rt_length=rt_length or len(ext)-primer_binding_length
 if rt_length<1 or primer_binding_length+rt_length>len(ext): raise ValueError("invalid reverse-transcription length")
 gc=gc_content(ext[-primer_binding_length:]); processivity=math.exp(-max(0,rt_length-25)/20)
 flap=1/(1+math.exp(-(rt_length-10)/5)); mismatch_bias=.75 if ext[primer_binding_length:primer_binding_length+1] in "GC" else .6
 return {"spacer":spacer,"extension":ext,"pbs_length":primer_binding_length,"rt_length":rt_length,"pbs_gc":gc,"rt_processivity":processivity,"flap_resolution":flap,"mismatch_repair_retention":mismatch_bias,"predicted_precise_fraction":processivity*flap*mismatch_bias}

def delivery_efficiency(mean=0.7,cv=0.2,size=1000,seed=0):
 mean=_unit(mean,"mean delivery efficiency")
 if cv<0 or size<1: raise ValueError("cv non-negative and size >= 1 required")
 if mean in (0,1): vals=np.full(size,mean)
 else:
  variance=(cv*mean)**2; common=mean*(1-mean)/max(variance,1e-12)-1; a=max(.01,mean*common); b=max(.01,(1-mean)*common); vals=np.random.default_rng(seed).beta(a,b,size)
 return {"mean":float(vals.mean()),"std":float(vals.std()),"quantiles":{str(q):float(np.quantile(vals,q)) for q in (.05,.5,.95)}}

def sequence_error_model(true_counts,error_rate=0.005):
 error_rate=_unit(error_rate,"error_rate"); counts={str(k):int(v) for k,v in true_counts.items()}
 if any(v<0 for v in counts.values()): raise ValueError("counts must be non-negative")
 total=sum(counts.values()); retained={k:v*(1-error_rate) for k,v in counts.items()}; spill=total*error_rate/max(1,len(counts))
 return {k:retained[k]+spill for k in counts}

def clonal_expansion(frequencies,generations=10,fitness=None):
 if generations<0: raise ValueError("generations must be non-negative")
 names=list(frequencies); f=np.array([frequencies[n] for n in names],float); w=np.array([(fitness or {}).get(n,1) for n in names],float)
 if np.any(f<0) or f.sum()<=0 or np.any(w<=0): raise ValueError("frequencies non-negative/nonzero and fitness positive required")
 f=f/f.sum()
 for _ in range(generations): f=f*w; f=f/f.sum()
 return dict(zip(names,map(float,f)))

def edit_precision(outcomes,desired="HDR"):
 if desired not in outcomes: raise ValueError("desired outcome missing")
 total=sum(float(outcomes.get(k,0)) for k in ("NHEJ","MMEJ","HDR"))
 return float(outcomes[desired])/total if total else 0.0

def functional_impact(frameshift,exonic=True,essentiality=0.5):
 frameshift=_unit(frameshift,"frameshift"); essentiality=_unit(essentiality,"essentiality")
 return frameshift*(1.0 if exonic else .15)*(.5+.5*essentiality)

def reward_decomposition(guide,background=None,chromatin=0.5,repair=None,desired="HDR",weights=None,length=20):
 g=_guide(guide,length); repair=repair or {"NHEJ":.7,"MMEJ":.2,"HDR":.1}; weights=weights or {"on_target":.3,"specificity":.2,"chromatin":.15,"repair":.2,"folding":.1,"functional":.05}
 if any(v<0 for v in weights.values()) or sum(weights.values())<=0: raise ValueError("reward weights must be non-negative with positive sum")
 off=score_off_targets(g,background,max_mismatches=3) if background else []; risk=min(1.0,sum(float(h["risk"]) for h in off if h["mismatches"]>0))
 # The vendored on-target heuristic is 20 nt only; other nuclease spacer
 # lengths get on_target=None and the reward renormalizes over the rest.
 components={"on_target":score_on_target(g) if len(g)==20 else None,"specificity":1-risk,"chromatin":_unit(chromatin,"chromatin"),"repair":edit_precision(repair,desired),"folding":rna_folding_score(g,len(g)),"functional":1-functional_impact(repair.get("frameshift",0),True,.5)}
 available={k:v for k,v in components.items() if v is not None}
 norm=sum(weights.values()) if len(available)==len(components) else sum(weights.get(k,0) for k in available)
 contributions={k:(v*weights.get(k,0)/norm if v is not None else None) for k,v in components.items()}
 return {"components":components,"contributions":contributions,"total":sum(v for v in contributions.values() if v is not None),"off_target_hits":len(off)}

def simulate_digital_lab(guide,contexts=None,replicates=96,seed=0,delivery_mean=.7,sequencing_error=.005):
 """Stochastic editing simulator with delivery, outcome, and read noise."""
 g=_guide(guide)
 if replicates<1: raise ValueError("replicates must be >= 1")
 contexts=contexts or [g+g]; rng=np.random.default_rng(seed); on=score_on_target(g); delivered=rng.binomial(1,delivery_mean,replicates); edited=[]; outcome_counts={"NHEJ":0,"MMEJ":0,"HDR":0,"unedited":0}
 for i,d in enumerate(delivered):
  if not d or rng.random()>on: outcome_counts["unedited"]+=1; edited.append(0); continue
  ro=repair_outcomes(contexts[i%len(contexts)]); choice=rng.choice(["NHEJ","MMEJ","HDR"],p=[ro["NHEJ"],ro["MMEJ"],ro["HDR"]]); outcome_counts[choice]+=1; edited.append(1)
 observed=sequence_error_model(outcome_counts,sequencing_error)
 return {"guide":g,"replicates":replicates,"seed":seed,"delivery_fraction":float(delivered.mean()),"edit_fraction":float(np.mean(edited)),"true_counts":outcome_counts,"observed_counts":observed}

def bayesian_posterior(successes,failures,prior_alpha=1.0,prior_beta=1.0):
 if min(successes,failures)<0 or min(prior_alpha,prior_beta)<=0: raise ValueError("counts non-negative and prior parameters positive required")
 a=prior_alpha+successes; b=prior_beta+failures; mean=a/(a+b); var=a*b/((a+b)**2*(a+b+1))
 return {"alpha":a,"beta":b,"mean":mean,"std":math.sqrt(var),"credible_95":[max(0,mean-1.96*math.sqrt(var)),min(1,mean+1.96*math.sqrt(var))]}

def ingest_sequencing_feedback(records,prior=None):
 """Update guide-specific Beta posteriors from validated count records."""
 state={k:dict(v) for k,v in (prior or {}).items()}; accepted=[]
 for rec in records:
  guide=_guide(rec["guide"]); edited=int(rec["edited_reads"]); total=int(rec["total_reads"])
  if not 0<=edited<=total: raise ValueError("edited_reads must be between zero and total_reads")
  old=state.get(guide,{"alpha":1.0,"beta":1.0}); state[guide]=bayesian_posterior(edited,total-edited,old["alpha"],old["beta"]); accepted.append(guide)
 return {"posterior":state,"accepted_records":len(accepted),"guides":sorted(set(accepted))}

def multiplex_compatibility(guides,minimum_distance=3):
 gs=[_guide(g) for g in guides]
 if len(set(gs))!=len(gs): raise ValueError("multiplex guides must be unique")
 pairs=[]; worst=1.0
 for i in range(len(gs)):
  for j in range(i+1,len(gs)):
   sim=guide_similarity(gs[i],gs[j]); distance=sum(a!=b for a,b in zip(gs[i],gs[j])); pairs.append({"i":i,"j":j,"similarity":sim,"hamming_distance":distance,"compatible":distance>=minimum_distance}); worst=min(worst,distance/20)
 return {"compatible":all(x["compatible"] for x in pairs),"pairs":pairs,"orthogonality":worst}

def enumerate_configurations(target,nucleases=None):
 """Enumerate concrete spacer/PAM configurations on the forward strand."""
 seq=clean_dna(target); names=nucleases or list(NUCLEASES); out=[]
 for name in names:
  if name not in NUCLEASES: raise ValueError(f"unknown nuclease {name!r}")
  cfg=NUCLEASES[name]; k=cfg["guide_length"]; p=cfg["pam"]
  if cfg.get("pam_side")=="5p":
   # Cas12a/CasX PAMs are 5' of the spacer (Zetsche et al. 2015; Liu et al.
   # 2019); the 3'-PAM loop below misses every valid site (BUG 66).
   for i in range(0,len(seq)-len(p)-k+1):
    pam=seq[i:i+len(p)]
    if pam_matches(pam,p): out.append({"nuclease":name,"guide":seq[i+len(p):i+len(p)+k],"pam":pam,"start":i+len(p),"end":i+len(p)+k,"cut_site":i+cfg["cut_offset"]})
  else:
   for i in range(k,len(seq)-len(p)+1):
    pam=seq[i:i+len(p)]
    if pam_matches(pam,p): out.append({"nuclease":name,"guide":seq[i-k:i],"pam":pam,"start":i-k,"end":i,"cut_site":i+cfg["cut_offset"]})
 return out

def rank_strategies(configurations,background=None,chromatin=0.5,repair_context=None,top_n=10):
 ranked=[]
 for config in configurations:
  length=NUCLEASES[config["nuclease"]]["guide_length"]
  ro=repair_outcomes(repair_context or config["guide"]*2,chromatin=chromatin); reward=reward_decomposition(config["guide"],background,chromatin,ro,length=length)
  ranked.append({**config,"reward":reward["total"],"reward_decomposition":reward["components"],"repair_outcomes":ro,"folding_score":rna_folding_score(config["guide"],length)})
 ranked.sort(key=lambda x:(-x["reward"],x.get("start",0),x["guide"]))
 return ranked[:top_n]

def policy_entropy(logits):
 probs=_softmax(np.asarray(logits,float),axis=1); return float(-np.sum(probs*np.log(np.maximum(probs,1e-15)),axis=1).mean())

def guide_diagnostics(guide,background=None,chromatin=.5,repair_context=None):
 """Flat scientific metrics; 32 by default, 35 with a background scan.

    Background-only specificity and hit count are omitted unless a background
    is provided. Sequence-position one-hot encodings are deliberately excluded.
    """
 g=_guide(guide); ro=repair_outcomes(repair_context or g*2,chromatin); rew=reward_decomposition(g,background,chromatin,ro); d={}
 d.update({"on_target":rew["components"]["on_target"],"specificity":rew["components"]["specificity"],"chromatin_prior":rew["components"]["chromatin"],"repair_precision":rew["components"]["repair"],"folding_score":rew["components"]["folding"],"functional_retention":rew["components"]["functional"],"total_reward":rew["total"],"gc_fraction":gc_content(g),"at_fraction":1-gc_content(g),"purine_fraction":sum(x in "AG" for x in g)/20,"pyrimidine_fraction":sum(x in "CT" for x in g)/20,"sequence_entropy_bits":-sum((g.count(b)/20)*math.log2(g.count(b)/20) for b in BASES if g.count(b))})
 # Correct explicit run-length calculation (the prior key is overwritten).
 d["homopolymer_max"]=float(max((j-i for i in range(20) for j in range(i+1,21) if len(set(g[i:j]))==1),default=1))
 for b in BASES: d[f"base_fraction.{b}"]=g.count(b)/20
 for name,value in ro.items(): d[f"repair.{name}"]=float(value)
 for name,value in rew["contributions"].items(): d[f"contribution.{name}"]=float(value)
 for editor in ("CBE","ABE"):
  result=base_editing_window(g,editor); d[f"{editor}.editable_count"]=float(len(result["editable_positions"]))
 d["poly_t_terminator"]=float("TTTT" in g); d["terminal_g"]=float(g[-1]=="G"); d["seed_gc_fraction"]=gc_content(g[-10:]); d["distal_gc_fraction"]=gc_content(g[:10])
 if background is not None:
  d["specificity_background_scan"]=d.pop("specificity")
  d["off_target_hit_count_background_scan"]=float(rew["off_target_hits"])
 else:
  d.pop("specificity")
  d.pop("contribution.specificity")
 return d

class MuseAgent:
 """Categorical policy-gradient guide designer with reproducible feedback."""
 BASES=BASES
 def __init__(self,seed=0,guide_length=20):
  if guide_length!=20: raise ValueError("current on-target model requires 20 nt guides")
  self.rng=np.random.default_rng(seed); self.logits=np.zeros((guide_length,4)); self.baseline=.5; self.rounds=0; self.history=[]; self.posterior={}; self.seed=seed
 def sample_guides(self,n=32):
  if n<1: raise ValueError("n must be >= 1")
  p=_softmax(self.logits,axis=1); return ["".join(BASES[int(self.rng.choice(4,p=p[i]))] for i in range(20)) for _ in range(n)]
 def reward(self,guide,pam="NGG",background=None,observed_efficiency=None,chromatin=.5,repair=None):
  if pam != "NGG" and not pam_matches(pam,"NGG"): raise ValueError("legacy Muse reward expects NGG pattern or a concrete SpCas9-compatible PAM")
  result=reward_decomposition(guide,background,chromatin,repair); r=result["total"]
  if observed_efficiency is not None: r=.6*r+.4*_unit(observed_efficiency,"observed_efficiency")
  return float(r)
 def update(self,samples,lr=.4,clip=.2):
  if not samples or lr<=0 or clip<=0: raise ValueError("samples/lr/clip must be non-empty and positive")
  rewards=np.array([float(r) for _,r in samples]); advantages=np.clip(rewards-self.baseline,-clip,clip)
  p=_softmax(self.logits,axis=1)
  for (guide,_),adv in zip(samples,advantages):
   g=_guide(guide)
   for i,b in enumerate(g):
    grad=-p[i].copy(); grad[BASES.index(b)]+=1; self.logits[i]+=lr*adv*grad
  self.logits-=self.logits.mean(axis=1,keepdims=True); self.baseline=.9*self.baseline+.1*float(rewards.mean()); self.rounds+=1
  summary={"round":self.rounds,"mean_reward":round(float(rewards.mean()),4),"best_reward":round(float(rewards.max()),4),"baseline":round(self.baseline,4),"policy_entropy":policy_entropy(self.logits)}; self.history.append(summary); return summary
 def best_guide(self):
  return "".join(BASES[int(i)] for i in np.argmax(self.logits,axis=1))
 def ingest_feedback(self,records):
  result=ingest_sequencing_feedback(records,self.posterior); self.posterior=result["posterior"]; return result
 def state_dict(self):
  return {"logits":self.logits.tolist(),"baseline":self.baseline,"rounds":self.rounds,"history":self.history,"posterior":self.posterior,"seed":self.seed}

def train_round(agent,background=None,n_samples=32,simulated_lab=True,chromatin=.5):
 guides=agent.sample_guides(n_samples); samples=[]
 for g in guides:
  obs=float(np.clip(score_on_target(g)+agent.rng.normal(0,.08),0,1)) if simulated_lab else None
  samples.append((g,agent.reward(g,background=background,observed_efficiency=obs,chromatin=chromatin)))
 summary=agent.update(samples); summary.update({"current_best_guide":agent.best_guide(),"best_guide_on_target":round(score_on_target(agent.best_guide()),3),"pam_compatibility":{k:v["pam"] for k,v in NUCLEASES.items()},"reward_model":"explicit mechanistic/heuristic decomposition; no trained model"}); return summary

def continual_learning_report(agent):
 rewards=[h["mean_reward"] for h in agent.history]
 return {"rounds":agent.rounds,"initial_mean_reward":rewards[0] if rewards else None,"latest_mean_reward":rewards[-1] if rewards else None,"reward_change":rewards[-1]-rewards[0] if len(rewards)>1 else 0.0,"policy_entropy":policy_entropy(agent.logits),"feedback_guides":len(agent.posterior),"model_status":"Explicit policy and Beta posterior; no trained CNN/transformer and not clinically validated."}

def export_simulation(strategy):
 return json.dumps(strategy,sort_keys=True,separators=(",",":"))

def design_muse_strategy(target,background=None,nucleases=None,chromatin=.5,repair_context=None,top_n=10):
 configs=enumerate_configurations(target,nucleases); ranked=rank_strategies(configs,background,chromatin,repair_context,top_n)
 return {"target_length":len(clean_dna(target)),"nucleases_considered":nucleases or list(NUCLEASES),"candidate_count":len(configs),"strategies":ranked,"traceability":{"reward_terms":["on_target","specificity","chromatin","repair","folding","functional"],"model_status":"No trained CNN/transformer; mechanistic and named heuristic surrogates only."},"next_steps":["Review ranked sequence/PAM configurations and causal score decomposition.","Validate top candidates with appropriate institutional controls before use.","Ingest count-level sequencing feedback to update guide-specific posteriors."]}
