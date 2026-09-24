from __future__ import annotations

WORKFLOWS = {
    "golden_gate": {
        "steps": [
            {"op": "dispense", "reagent": "DNA parts (equimolar 40 fmol)", "plate": "PCR-96"},
            {"op": "dispense", "reagent": "BsaI-HFv2 1 uL", "plate": "PCR-96"},
            {"op": "dispense", "reagent": "T4 ligase + buffer", "plate": "PCR-96"},
            {"op": "thermocycle", "program": "30x(37C 5min, 16C 5min), 50C 10min, 80C 10min"},
            {"op": "transform", "cells": "DH5-alpha competent", "method": "heat shock 42C 45s"},
            {"op": "plate", "media": "LB + selection", "incubate_h": 16},
            {"op": "pick_colonies", "n": 8, "into": "deepwell-96 + media"},
            {"op": "screen", "method": "colony PCR + gel"},
        ],
        "equipment": ["liquid handler", "thermocycler", "colony picker", "plate reader"],
    },
    "gibson": {
        "steps": [
            {"op": "dispense", "reagent": "PCR fragments (0.03 pmol each)", "plate": "PCR-96"},
            {"op": "dispense", "reagent": "Gibson mastermix 2x", "plate": "PCR-96"},
            {"op": "incubate", "temp_c": 50, "min": 60},
            {"op": "transform", "cells": "NEB-stable competent"},
            {"op": "plate", "media": "LB + selection"},
        ],
        "equipment": ["liquid handler", "incubator", "colony picker"],
    },
    "pcr_screen": {
        "steps": [
            {"op": "dispense", "reagent": "template + primers + polymerase mix"},
            {"op": "thermocycle", "program": "98C 30s; 30x(98C 10s, 60C 20s, 72C 30s/kb); 72C 5min"},
            {"op": "gel", "agarose_pct": 1.0},
        ],
        "equipment": ["liquid handler", "thermocycler", "gel rig"],
    },
}


def generate_protocol(workflow: str, n_constructs: int = 8,
                      optimization: bool = True) -> dict:
    """Generate a biofoundry-ready robotic protocol with optimization tips."""
    if workflow not in WORKFLOWS:
        raise KeyError(f"unknown workflow {workflow!r}; have {sorted(WORKFLOWS)}")
    wf = WORKFLOWS[workflow]
    plates = (n_constructs + 95) // 96
    est_min = sum(_step_minutes(s) for s in wf["steps"]) * plates
    return {
        "workflow": workflow,
        "n_constructs": n_constructs,
        "plates": plates,
        "steps": wf["steps"],
        "equipment_required": wf["equipment"],
        "estimated_runtime_min": est_min,
        "optimization_tips": _tips(workflow) if optimization else [],
        "screening": {"candidates": n_constructs * 8,
                      "recommended_controls": ["no-DNA negative", "known-good positive",
                                               "assembly-vector-only"]},
    }


def _step_minutes(step: dict) -> int:
    return {"dispense": 8, "thermocycle": 120, "transform": 45, "plate": 5,
            "pick_colonies": 20, "screen": 60, "incubate": 60, "gel": 45}.get(step["op"], 15)


def _tips(workflow: str) -> list[str]:
    common = ["pre-wet tips for viscous enzyme mixes",
              "keep ligase on cold block; freeze-thaw kills activity",
              "run Bayesian optimization over annealing temp if success < 80%"]
    if workflow == "golden_gate":
        common.append("check parts for internal BsaI sites; domesticate silently first")
    return common

import math, json
from collections import defaultdict

def workflow_dag(steps):
 nodes=[{'id':i,**s} for i,s in enumerate(steps)]; edges=[{'source':i,'target':i+1,'material_flow':True} for i in range(len(steps)-1)]; return {'nodes':nodes,'edges':edges,'topological_order':list(range(len(steps)))}
def schedule_resources(protocol,equipment_capacity=None):
 cap=equipment_capacity or {}; available=defaultdict(float); schedule=[]
 prev_end=0.0
 for i,s in enumerate(protocol['steps']):
  eq=s.get('equipment',s['op']); duration=_step_minutes(s)
  # a step needs both its resource free and its DAG predecessor finished
  start=max(available[eq],prev_end); schedule.append({'step':i,'operation':s['op'],'resource':eq,'start_min':start,'end_min':start+duration}); available[eq]=start+duration; prev_end=start+duration
 return {'schedule':schedule,'makespan_min':max((x['end_min'] for x in schedule),default=0),'utilization':{k:v/max(1,max(available.values())) for k,v in available.items()}}
def bayesian_condition(prior_mean,prior_variance,observations,noise_variance):
 precision=1/prior_variance+len(observations)/noise_variance; mean=(prior_mean/prior_variance+sum(observations)/noise_variance)/precision; return {'posterior_mean':mean,'posterior_variance':1/precision,'n_observations':len(observations)}
def pid_control(setpoint,measurements,kp=.5,ki=.1,kd=.05,dt=1):
 integ=0; prev=0; controls=[]
 for m in measurements:
  err=setpoint-m; integ+=err*dt; controls.append(kp*err+ki*integ+kd*(err-prev)/dt); prev=err
 return {'controls':controls,'final_error':setpoint-measurements[-1],'integral_error':integ}
def reagent_activity(initial_activity,age_days,half_life_days,lot_factor=1): return {'activity_fraction':lot_factor*2**(-age_days/half_life_days),'compensation_factor':1/max(1e-9,lot_factor*2**(-age_days/half_life_days))}
def assay_quality(signal,background):
 mean_s=sum(signal)/len(signal); mean_b=sum(background)/len(background); var_s=sum((x-mean_s)**2 for x in signal)/(len(signal)-1); var_b=sum((x-mean_b)**2 for x in background)/(len(background)-1); z=1-3*(math.sqrt(var_s)+math.sqrt(var_b))/abs(mean_s-mean_b); return {'z_prime':z,'signal_background':mean_s/max(1e-9,mean_b),'robust':z>.5}
def reroute_on_failure(dag,failed_step,fallback):
 nodes=list(dag['nodes'])+[{'id':len(dag['nodes']),**fallback}]; edges=[e for e in dag['edges'] if e['source']!=failed_step]+[{'source':failed_step,'target':len(nodes)-1,'condition':'failure'}]; return {'nodes':nodes,'edges':edges,'failed_step':failed_step,'fallback_id':len(nodes)-1}
def experiment_log(protocol,results): return {'protocol':protocol,'results':results,'machine_readable':json.dumps({'workflow':protocol['workflow'],'results':results},sort_keys=True),'provenance':{'generator':'BioFactory 1-A','version':'explicit-model-v1'}}
def dbtl_report(workflow,n_constructs=8,observations=(.6,.8,.9),assay_signal=(10,11,9.5),assay_background=(1,1.2,.8)):
 p=generate_protocol(workflow,n_constructs); dag=workflow_dag(p['steps']); return {'protocol':p,'dag':dag,'schedule':schedule_resources(p),'condition_update':bayesian_condition(.7,.1,list(observations),.05),'assay_quality':assay_quality(list(assay_signal),list(assay_background)),'model_status':'Deterministic workflow, Bayesian update and control utilities; no AI optimizer or live hardware connection is bundled.'}
def factory_diagnostics(r):
 p=r['protocol']; d=r['dag']; s=r['schedule']; b=r['condition_update']; q=r['assay_quality']; return {'construct_count':float(p['n_constructs']),'plate_count':float(p['plates']),'step_count':float(len(p['steps'])),'equipment_count':float(len(p['equipment_required'])),'estimated_runtime':float(p['estimated_runtime_min']),'dag_nodes':float(len(d['nodes'])),'dag_edges':float(len(d['edges'])),'makespan':float(s['makespan_min']),'posterior_mean':b['posterior_mean'],'posterior_variance':b['posterior_variance'],'z_prime':q['z_prime'],'signal_background':q['signal_background']}
