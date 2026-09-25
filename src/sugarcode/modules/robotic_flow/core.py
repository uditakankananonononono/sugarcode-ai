from __future__ import annotations

LIQUID_CLASSES = {
    "water": {"viscosity_cp": 1.0, "aspirate_speed_ul_s": 200, "air_gap_ul": 2},
    "glycerol_50": {"viscosity_cp": 6.0, "aspirate_speed_ul_s": 40, "air_gap_ul": 4},
    "enzyme_mix": {"viscosity_cp": 2.5, "aspirate_speed_ul_s": 80, "air_gap_ul": 3},
    "cells": {"viscosity_cp": 1.2, "aspirate_speed_ul_s": 100, "air_gap_ul": 2},
}


def pipette_plan(transfers: list[dict]) -> dict:
    """Convert transfer list to calibrated liquid-class handling steps.

    Each transfer: {"source": well, "dest": well, "volume_ul": x, "liquid": class}
    Applies viscosity-dependent speeds, air gaps and evaporation correction.
    """
    steps = []
    total_s = 0.0
    for i, t in enumerate(transfers):
        liquid = t.get("liquid", "water")
        if liquid not in LIQUID_CLASSES:
            # was: silently calibrated with water's speeds while labelling
            # the step with the unknown class (e.g. "mercury" at 200 ul/s)
            raise KeyError(f"unknown liquid class {liquid!r}; have {sorted(LIQUID_CLASSES)}")
        lc = LIQUID_CLASSES[liquid]
        vol = t["volume_ul"]
        asp_t = vol / lc["aspirate_speed_ul_s"]
        evap = round(vol * 0.002 * (asp_t / 60), 4)
        steps.append({
            "step": i + 1, "source": t["source"], "dest": t["dest"],
            "volume_ul": vol, "liquid_class": t.get("liquid", "water"),
            "aspirate_speed_ul_s": lc["aspirate_speed_ul_s"],
            "air_gap_ul": lc["air_gap_ul"],
            "evaporation_correction_ul": evap,
            "estimated_s": round(2 * asp_t + 3, 1),
        })
        total_s += 2 * asp_t + 3
    return {"n_transfers": len(steps), "steps": steps,
            "estimated_total_min": round(total_s / 60, 1)}


def schedule_run(tasks: list[dict]) -> dict:
    """Greedy list-scheduling of deck tasks onto shared instruments.

    tasks: [{"id": str, "instrument": str, "duration_min": x, "after": [ids]}]
    Returns instrument timelines with makespan.
    """
    ids = [t["id"] for t in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate task ids make the schedule ambiguous")
    unknown = {d for t in tasks for d in t.get("after", []) if d not in set(ids)}
    if unknown:
        # was: misreported as "dependency cycle in task graph"
        raise ValueError(f"unknown dependencies: {sorted(unknown)}")
    done: dict[str, float] = {}
    instrument_free: dict[str, float] = {}
    timeline: list[dict] = []
    pending = list(tasks)
    guard = 0
    while pending and guard < 10000:
        guard += 1
        progressed = False
        for t in list(pending):
            deps = t.get("after", [])
            if all(d in done for d in deps):
                ready = max([done[d] for d in deps], default=0.0)
                start = max(ready, instrument_free.get(t["instrument"], 0.0))
                end = start + t["duration_min"]
                timeline.append({"id": t["id"], "instrument": t["instrument"],
                                 "start_min": round(start, 1), "end_min": round(end, 1)})
                instrument_free[t["instrument"]] = end
                done[t["id"]] = end
                pending.remove(t)
                progressed = True
        if not progressed:
            raise ValueError("dependency cycle in task graph")
    makespan = max((x["end_min"] for x in timeline), default=0.0)
    return {"timeline": sorted(timeline, key=lambda x: x["start_min"]),
            "makespan_min": round(makespan, 1),
            "instrument_utilization": _utilization(timeline, makespan)}


def _utilization(timeline: list[dict], makespan: float) -> dict:
    busy: dict[str, float] = {}
    for x in timeline:
        busy[x["instrument"]] = busy.get(x["instrument"], 0.0) + (x["end_min"] - x["start_min"])
    return {k: round(v / makespan, 3) if makespan else 0.0 for k, v in busy.items()}


def monitor(run: dict, checkpoints: list[dict] | None = None) -> dict:
    """Real-time monitoring model: expected vs observed checkpoint times."""
    checkpoints = checkpoints or []
    alerts = []
    for cp in checkpoints:
        drift = cp.get("observed_min", cp["expected_min"]) - cp["expected_min"]
        if abs(drift) > cp.get("tolerance_min", 5):
            alerts.append({"task": cp["task"], "drift_min": round(drift, 1),
                           "severity": "warn" if abs(drift) < 15 else "critical"})
    return {
        "run_makespan_min": run.get("makespan_min"),
        "checkpoints": checkpoints,
        "alerts": alerts,
        "precision_note": "all timing tracked to the minute; volume QC via liquid-class calibration",
        "status": "on_track" if not alerts else "review_required",
    }

import math
from collections import defaultdict

def droplet_error(volume_ul,viscosity_cp,surface_tension=72,temp_c=22):
 bias=.002*viscosity_cp+.001*abs(surface_tension-72)+.0005*abs(temp_c-22); return {'bias_ul':volume_ul*bias,'delivered_ul':volume_ul*(1-bias),'relative_error':bias}
def environmental_control(setpoint,observations,kp=.5,ki=.05):
 integ=0; control=[]
 for x in observations: err=setpoint-x; integ+=err; control.append(kp*err+ki*integ)
 return {'control':control,'final_error':setpoint-observations[-1],'integral_error':integ}
def sensor_anomalies(observations,z_threshold=3):
 vals=[float(x) for x in observations]; mean=sum(vals)/len(vals); sd=math.sqrt(sum((x-mean)**2 for x in vals)/max(1,len(vals)-1)); return {'mean':mean,'std':sd,'anomalies':[i for i,x in enumerate(vals) if abs(x-mean)>z_threshold*max(sd,1e-9)]}
def sample_lineage(samples,operations):
 lineage={s:{'parents':[],'operations':[]} for s in samples}
 for op in operations:
  out=op['output']; lineage[out]={'parents':list(op.get('inputs',[])),'operations':[op['op']]}
 # traceable was trivially True ('parents' always exists); check that every
 # parent is itself a known sample in the lineage
 unknown=sorted({p for x in lineage.values() for p in x['parents'] if p not in lineage})
 return {'samples':lineage,'unknown_parents':unknown,'traceable':not unknown}
def reagent_status(age_days,half_life_days,temperature_excursion_h=0,incompatible=False):
 activity=2**(-age_days/half_life_days)*math.exp(-.03*temperature_excursion_h); return {'activity_fraction':activity,'usable':activity>.7 and not incompatible,'incompatible':incompatible}
def contamination_control(transfers):
 last=None; actions=[]
 for t in transfers:
  group=t.get('contamination_group',t.get('liquid','water'))
  if last is not None and group!=last: actions.append({'before_transfer':t['dest'],'action':'new_tip_and_wash'})
  last=group
 return {'actions':actions,'tip_changes':len(actions)}
def corrective_action(alert):
 severity=alert['severity']; return {'alert':alert,'action':'pause_and_isolate' if severity=='critical' else 'recalibrate_and_retry','requires_human_review':severity=='critical'}
def robotic_report(transfers,tasks,checkpoints=()):
 p=pipette_plan(transfers); run=schedule_run(tasks); mon=monitor(run,list(checkpoints)); return {'pipetting':p,'schedule':run,'monitoring':mon,'contamination':contamination_control(transfers),'corrective_actions':[corrective_action(a) for a in mon['alerts']],'model_status':'Deterministic fluid/timing/control models; no computer vision or live robot hardware connection is bundled.'}
def robotic_diagnostics(r):
 p=r['pipetting']; s=r['schedule']; m=r['monitoring']; return {'transfer_count':float(p['n_transfers']),'pipette_minutes':p['estimated_total_min'],'total_volume':sum(x['volume_ul'] for x in p['steps']),'evaporation_correction':sum(x['evaporation_correction_ul'] for x in p['steps']),'makespan':s['makespan_min'],'instrument_count':float(len(s['instrument_utilization'])),'mean_utilization':sum(s['instrument_utilization'].values())/max(1,len(s['instrument_utilization'])),'checkpoint_count':float(len(m['checkpoints'])),'alert_count':float(len(m['alerts'])),'critical_count':float(sum(a['severity']=='critical' for a in m['alerts'])),'tip_changes':float(r['contamination']['tip_changes']),'corrective_count':float(len(r['corrective_actions']))}
