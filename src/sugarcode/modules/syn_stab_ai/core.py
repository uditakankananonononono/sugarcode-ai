from __future__ import annotations
from ..stability_ai.core import stability_forecast


def evaluate_circuit_stability(circuit: dict) -> dict:
    """Circuit-level evolutionary stability: burden from expression load,
    failure risk per gate, generation-resolved forecast."""
    n_gates = circuit.get("n_gates", 3)
    expression = circuit.get("expression_level", 0.5)
    mode = circuit.get("mode", "plasmid")
    size_kb = circuit.get("size_kb", 4.0 * n_gates / 3)
    burden = min(1.0, 0.25 * n_gates * expression)
    fc = stability_forecast({"mode": mode, "burden": burden, "size_kb": size_kb,
                             "toxic": circuit.get("toxic", False)},
                            generations=circuit.get("generations", 200))
    return {
        "circuit": circuit,
        "estimated_burden": round(burden, 3),
        "forecast": fc,
        "circuit_failure_risk": round(1 - fc["trajectory"][-1]["functional_fraction"], 3),
        "dominant_risk": ("mutational drift" if mode == "genomic" else "plasmid loss + burden selection"),
    }


def suggest_stabilization(circuit: dict) -> dict:
    """Genetic modifications to increase functional half-life."""
    ev = evaluate_circuit_stability(circuit)
    suggestions = []
    if circuit.get("mode", "plasmid") == "plasmid":
        suggestions.append({"change": "integrate circuit into genome",
                            "expected_half_life_gain": "5-20x",
                            "mechanism": "removes segregational loss"})
    if ev["estimated_burden"] > 0.4:
        suggestions.append({"change": "swap to weaker promoter / tune RBS",
                            "expected_half_life_gain": "2-4x",
                            "mechanism": "lowers burden, weakens selection against circuit"})
    suggestions.append({"change": "remove repetitive parts; diversify promoters/terminators",
                        "expected_half_life_gain": "1.5-3x",
                        "mechanism": "suppresses homologous-recombination deletions"})
    suggestions.append({"change": "add toxin-antitoxin or addiction module",
                        "expected_half_life_gain": "2-5x",
                        "mechanism": "cells losing the circuit die"})
    return {"evaluation": ev, "suggestions": suggestions}
import math, random
from collections import Counter

def sequence_risk(seq):
 s=''.join(x for x in seq.upper() if x in 'ACGT'); gc=(s.count('G')+s.count('C'))/max(1,len(s)); repeats=max((s.count(s[i:i+k]) for k in range(2,9) for i in range(max(0,len(s)-k+1))),default=0); pal=sum(s[i:i+6]==s[i:i+6][::-1] for i in range(max(0,len(s)-5))); return {'gc_fraction':gc,'gc_extreme':abs(gc-.5)*2,'repeat_burden':repeats/max(1,len(s)),'palindrome_count':pal,'mutation_risk':min(1,abs(gc-.5)+repeats/max(1,len(s))+.05*pal)}
def resource_burden(ribosome_fraction,atp_fraction,cofactor_fraction,toxic_intermediate=0): return {'total':min(1,.4*ribosome_fraction+.3*atp_fraction+.2*cofactor_fraction+.1*toxic_intermediate),'components':{'ribosome':ribosome_fraction,'atp':atp_fraction,'cofactor':cofactor_fraction,'toxicity':toxic_intermediate}}
def population_simulation(initial_functional=1,mutation_rate=.001,selection_cost=.01,drift_population=1000,generations=100,seed=0):
 rng=random.Random(seed); f=initial_functional; trace=[]
 for g in range(generations+1):
  trace.append(f); expected=f*(1-mutation_rate)*(1-selection_cost)/(1-f*selection_cost); f=max(0,min(1,rng.gauss(expected,math.sqrt(max(expected*(1-expected),0)/drift_population))))
 return {'functional_fraction':trace,'failure_probability':1-trace[-1],'half_life_generation':next((i for i,x in enumerate(trace) if x<.5),None)}
def chemical_stress(oxidative=.1,ph=7.4,reactive=.1): return {'damage_rate':min(1,.5*oxidative+.2*abs(ph-7.4)+.3*reactive),'oxidative':oxidative,'ph_deviation':abs(ph-7.4),'reactive':reactive}
def fitness_landscape(mutations,base_fitness=1):
 rows=[{**m,'fitness':base_fitness-float(m.get('burden_relief',0))*(-1)-float(m.get('functional_loss',0))} for m in mutations]; return {'mutations':rows,'favored':sorted(rows,key=lambda x:-x['fitness'])}
def compare_stabilization(circuit,strategies):
 base=evaluate_circuit_stability(circuit); out=[]
 for s in strategies:
  c={**circuit}; c['expression_level']=c.get('expression_level',.5)*float(s.get('expression_factor',1)); c['mode']=s.get('mode',c.get('mode','plasmid')); ev=evaluate_circuit_stability(c); out.append({**s,'failure_risk':ev['circuit_failure_risk'],'risk_reduction':base['circuit_failure_risk']-ev['circuit_failure_risk']})
 return sorted(out,key=lambda x:-x['risk_reduction'])
def stability_report(circuit,sequence=''):
 e=evaluate_circuit_stability(circuit); seq=sequence_risk(sequence) if sequence else None; burden=resource_burden(e['estimated_burden'],.2,.1,float(circuit.get('toxic',False))); pop=population_simulation(mutation_rate=.001+(seq['mutation_risk']*.01 if seq else 0),selection_cost=burden['total']*.05,seed=1); return {'evaluation':e,'sequence_risk':seq,'resource_burden':burden,'population':pop,'chemical_stress':chemical_stress(),'recommendations':suggest_stabilization(circuit),'model_status':'Explicit sequence, burden and Wright-Fisher-like simulation; no trained predictor and not validated for deployment decisions.'}
def stability_diagnostics(r):
 s=r['sequence_risk'] or {'gc_fraction':0,'repeat_burden':0,'palindrome_count':0,'mutation_risk':0}; p=r['population']; c=r['chemical_stress']; return {'estimated_burden':r['evaluation']['estimated_burden'],'circuit_failure_risk':r['evaluation']['circuit_failure_risk'],'gc_fraction':s['gc_fraction'],'repeat_burden':s['repeat_burden'],'palindrome_count':float(s['palindrome_count']),'sequence_mutation_risk':s['mutation_risk'],'resource_burden':r['resource_burden']['total'],'population_failure':p['failure_probability'],'final_functional':p['functional_fraction'][-1],'damage_rate':c['damage_rate'],'suggestion_count':float(len(r['recommendations']['suggestions'])),'trajectory_length':float(len(p['functional_fraction']))}
