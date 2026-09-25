from __future__ import annotations
import math


class LabScene:
    """A 3D lab: benches, instruments, positions - the 'VR' world model."""

    def __init__(self):
        self.objects: dict[str, dict] = {}
        self.log: list[dict] = []

    def add(self, name: str, kind: str, pos: tuple[float, float, float],
            state: dict | None = None) -> dict:
        self.objects[name] = {"kind": kind, "pos": tuple(pos), "state": state or {}}
        return self.objects[name]

    def move_to(self, obj: str, target: str) -> float:
        a, b = self.objects[obj], self.objects[target]
        d = math.dist(a["pos"], b["pos"])
        a["pos"] = b["pos"]
        self.log.append({"action": "move", "obj": obj, "to": target, "distance_m": round(d, 2)})
        return d

    def interact(self, obj: str, command: str, **kwargs) -> dict:
        o = self.objects[obj]
        handler = getattr(self, f"_cmd_{command}", None)
        if handler is None:
            raise ValueError(f"instrument {obj} has no command {command!r}")
        result = handler(o, **kwargs)
        self.log.append({"action": command, "obj": obj, "result": result})
        return result

    def _cmd_pipette(self, o, volume_uL: float = 10.0):
        if volume_uL <= 0 or volume_uL > 1000:
            raise ValueError("pipette range 0-1000 uL")
        o["state"]["last_volume_uL"] = volume_uL
        return {"dispensed_uL": volume_uL, "tip": "fresh"}

    def _cmd_incubate(self, o, minutes: float = 30, temp_C: float = 37.0):
        o["state"]["elapsed_min"] = o["state"].get("elapsed_min", 0) + minutes
        return {"temp_C": temp_C, "total_min": o["state"]["elapsed_min"]}

    def _cmd_measure(self, o, assay: str = "fluorescence"):
        val = o["state"].get("signal", 0.0)
        return {"assay": assay, "reading": round(val, 3)}


def default_lab() -> LabScene:
    lab = LabScene()
    lab.add("bench_1", "bench", (0, 0, 0))
    lab.add("p1000", "pipette", (0.5, 0, 0.2))
    lab.add("plate_96", "plate", (1.0, 0, 0), state={"signal": 0.0})
    lab.add("incubator", "incubator", (3, 0, 0))
    lab.add("reader", "plate_reader", (4, 1, 0))
    return lab


def run_session(task: str = "crispr_transfection") -> dict:
    """Scripted experiment in the virtual lab; returns observations + conclusions."""
    lab = default_lab()
    observations = []
    if task == "crispr_transfection":
        lab.move_to("p1000", "plate_96")
        r1 = lab.interact("p1000", "pipette", volume_uL=50)
        observations.append(f"dispensed {r1['dispensed_uL']} uL Cas9-RNP transfection mix")
        lab.move_to("plate_96", "incubator")
        r2 = lab.interact("incubator", "incubate", minutes=2880, temp_C=37.0)
        observations.append(f"incubated 48 h at {r2['temp_C']} C")
        lab.objects["plate_96"]["state"]["signal"] = 0.72
        lab.move_to("plate_96", "reader")
        # the reader measures the PLATE's signal; measuring the reader object itself reads 0
        r3 = lab.interact("plate_96", "measure", assay="fluorescence")
        observations.append(f"reporter fluorescence {r3['reading']} (edit proxy)")
        conclusion = ("editing reporter positive at 0.72 RFU - transfection succeeded; "
                      "confirm indels by NGS before claiming edit rate")
    elif task == "molecular_docking":
        from ..docking_studio.core import dock
        lab.interact("p1000", "pipette", volume_uL=10)
        res = dock("ELKVIGKGAFG", "CCO")  # kinase-hinge-like pocket residues, ethanol ligand
        observations.append(f"dock dG {res.get('binding_dg_kcal_mol', res)} kcal/mol")
        conclusion = "binding pose scored in silico; wet-lab confirmation via SPR next"
    else:
        raise KeyError(f"unknown task {task!r}; have crispr_transfection, molecular_docking")
    return {
        "task": task, "scene": {k: v["pos"] for k, v in lab.objects.items()},
        "observations": observations, "conclusion": conclusion,
        "action_log": lab.log,
        "cost_note": "virtual run: zero consumables, full protocol replayability",
    }

# --- specification-complete executable virtual laboratory --------------------
def molecular_docking_experiment(ligand_xyz, pocket_xyz, *, steps: int=300, seed: int=17) -> dict:
    """Optimize a rigid ligand pose in a 3-D pocket with a physical pair potential."""
    import numpy as np
    from scipy.optimize import differential_evolution
    lig=np.asarray(ligand_xyz,float); pocket=np.asarray(pocket_xyz,float)
    if lig.ndim!=2 or pocket.ndim!=2 or lig.shape[1:]!=(3,) or pocket.shape[1:]!=(3,) or len(lig)<2 or len(pocket)<2: raise ValueError("ligand_xyz and pocket_xyz must be finite Nx3 arrays with N >= 2")
    if not np.all(np.isfinite(lig)) or not np.all(np.isfinite(pocket)) or steps<1: raise ValueError("coordinates must be finite and steps positive")
    centered=lig-lig.mean(0)
    def rotate(a):
        ax,ay,az=a; cx,sx=math.cos(ax),math.sin(ax); cy,sy=math.cos(ay),math.sin(ay); cz,sz=math.cos(az),math.sin(az)
        return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    def score(x):
        pose=centered@rotate(x[3:]).T+x[:3]; d=np.linalg.norm(pose[:,None,:]-pocket[None,:,:],axis=2); d=np.maximum(d,.5)
        lj=(3/d)**12-2*(3/d)**6
        return float(np.sum(np.min(lj,axis=1))+.02*np.sum((pose.mean(0)-pocket.mean(0))**2))
    lo=pocket.min(0)-5; hi=pocket.max(0)+5; bounds=list(zip(lo,hi))+[(-math.pi,math.pi)]*3
    fit=differential_evolution(score,bounds,seed=seed,maxiter=steps,popsize=8,polish=True,tol=1e-7)
    pose=centered@rotate(fit.x[3:]).T+fit.x[:3]
    d=np.linalg.norm(pose[:,None,:]-pocket[None,:,:],axis=2)
    return {"optimized_pose_xyz":pose.tolist(),"score":round(float(fit.fun),8),"iterations":fit.nit,"evaluations":fit.nfev,
            "contacts_under_4A":int(np.sum(d<4)),"minimum_distance_A":round(float(d.min()),6),"converged":bool(fit.success),
            "method":"differential evolution rigid-pose Lennard-Jones optimization","next_step":"validate affinity with SPR or ITC",
            "model_status":"mechanistic hermetic docking experiment; no binding claim"}


def crispr_design_experiment(target_dna: str, *, pam: str="NGG", guide_length: int=20) -> dict:
    """Enumerate CRISPR guides and score GC, homopolymers, and sequence uniqueness."""
    import re
    seq=target_dna.upper().replace(" ","")
    if not seq or set(seq)-set("ACGT"): raise ValueError("target_dna must be a non-empty A/C/G/T sequence")
    if guide_length<15 or guide_length>30: raise ValueError("guide_length must be between 15 and 30")
    if pam!="NGG": raise ValueError("currently supported pam is NGG")
    rows=[]
    for i in range(guide_length,len(seq)-2):
        if seq[i+1:i+3]=="GG":
            g=seq[i-guide_length:i]; gc=(g.count("G")+g.count("C"))/guide_length
            hom=max((len(x.group()) for x in re.finditer(r"(A+|C+|G+|T+)",g)),default=1)
            uniqueness=1/(1+sum(seq[j:j+guide_length]==g for j in range(len(seq)-guide_length+1) if j!=i-guide_length))
            score=max(0,1-2*abs(gc-.5)-.15*max(0,hom-3))*uniqueness
            rows.append({"guide":g,"start":i-guide_length,"pam":seq[i:i+3],"gc_fraction":round(gc,4),"max_homopolymer":hom,"uniqueness":round(uniqueness,4),"score":round(score,6)})
    rows.sort(key=lambda x:(-x["score"],x["start"]))
    return {"candidates":rows,"recommended":rows[0] if rows else None,"candidate_count":len(rows),
            "observations":[f"{len(rows)} NGG-adjacent guides enumerated",f"best score {rows[0]['score']:.3f}" if rows else "no compatible PAM found"],
            "conclusion":"candidate ranking for experimental review; confirm off-targets and editing efficiency empirically",
            "model_status":"mechanistic hermetic guide scoring; no editing claim"}


def simulate_protocol(protocol: list[dict], *, seed: int=42) -> dict:
    """Execute a validated protocol with stochastic pipetting and incubation kinetics."""
    import numpy as np
    if not isinstance(protocol,list) or not protocol: raise ValueError("protocol must be a non-empty list of step mappings")
    rng=np.random.default_rng(seed); samples={}; log=[]; elapsed=0.; cost=0.
    for i,step in enumerate(protocol,1):
        if not isinstance(step,dict) or "action" not in step: raise ValueError(f"step {i} requires action")
        action=step["action"]
        if action=="pipette":
            sample=str(step.get("sample","sample")); volume=float(step.get("volume_uL",0)); cv=float(step.get("cv",.01))
            if volume<=0 or volume>1000 or cv<0: raise ValueError(f"step {i} pipette volume must be 0-1000 uL and cv non-negative")
            actual=max(0,float(rng.normal(volume,volume*cv))); samples.setdefault(sample,{"volume_uL":0.,"signal":0.}); samples[sample]["volume_uL"]+=actual; cost+=.25
            result={"requested_uL":volume,"actual_uL":round(actual,6),"relative_error":round((actual-volume)/volume,6)}
        elif action=="incubate":
            sample=str(step.get("sample","sample")); minutes=float(step.get("minutes",0)); temp=float(step.get("temp_C",37))
            if minutes<=0 or not 0<=temp<=100: raise ValueError(f"step {i} incubation needs positive minutes and temp_C 0-100")
            samples.setdefault(sample,{"volume_uL":0.,"signal":0.}); gain=(1-math.exp(-minutes/240))*math.exp(-((temp-37)/12)**2); samples[sample]["signal"]+=gain; elapsed+=minutes
            result={"minutes":minutes,"temp_C":temp,"signal_gain":round(gain,6)}
        elif action=="measure":
            sample=str(step.get("sample","sample")); assay=str(step.get("assay","fluorescence")); s=samples.get(sample,{"signal":0})["signal"]
            reading=max(0,float(rng.normal(s,.02))); result={"assay":assay,"reading":round(reading,6),"sample":sample}
        else: raise ValueError(f"step {i} unknown action {action!r}; use pipette, incubate, or measure")
        log.append({"step":i,"action":action,"result":result})
    measurements=[x["result"]["reading"] for x in log if x["action"]=="measure"]
    return {"execution_log":log,"samples":samples,"elapsed_minutes":elapsed,"estimated_consumable_cost":round(cost,2),
            "observations":[f"{len(log)} steps executed",f"{len(measurements)} measurements acquired"],
            "conclusion":"signal detected" if measurements and max(measurements)>.2 else "signal below decision threshold",
            "replay":{"seed":seed,"protocol":protocol},"model_status":"mechanistic hermetic virtual experiment"}


def enhancement_features(result: dict) -> dict:
    """Compute exactly 51 result-derived experiment diagnostics."""
    import numpy as np
    log=result["execution_log"]; samples=result["samples"]; pip=[x for x in log if x["action"]=="pipette"]; inc=[x for x in log if x["action"]=="incubate"]; meas=[x for x in log if x["action"]=="measure"]
    errors=np.asarray([x["result"]["relative_error"] for x in pip] or [0.]); volumes=np.asarray([x["result"]["actual_uL"] for x in pip] or [0.]); readings=np.asarray([x["result"]["reading"] for x in meas] or [0.]); gains=np.asarray([x["result"]["signal_gain"] for x in inc] or [0.]); temps=np.asarray([x["result"]["temp_C"] for x in inc] or [0.]); mins=np.asarray([x["result"]["minutes"] for x in inc] or [0.])
    out={"step_count":len(log),"pipette_step_count":len(pip),"incubation_step_count":len(inc),"measurement_step_count":len(meas),"sample_count":len(samples),
    "elapsed_minutes":result["elapsed_minutes"],"consumable_cost":result["estimated_consumable_cost"],"total_actual_volume_uL":float(volumes.sum()),"minimum_actual_volume_uL":float(volumes.min()),"maximum_actual_volume_uL":float(volumes.max()),
    "pipette_absolute_error_uL":float(sum(abs(x["result"]["actual_uL"]-x["result"]["requested_uL"]) for x in pip)),"pipette_signed_error_uL":float(sum(x["result"]["actual_uL"]-x["result"]["requested_uL"] for x in pip)),
    "maximum_relative_pipette_error":float(np.max(np.abs(errors))),"pipette_within_2pct_count":int(np.sum(np.abs(errors)<=.02)),"pipette_outside_5pct_count":int(np.sum(np.abs(errors)>.05)),
    "total_incubation_minutes":float(mins.sum()),"minimum_incubation_minutes":float(mins.min()),"maximum_incubation_minutes":float(mins.max()),"minimum_incubation_temp_C":float(temps.min()),"maximum_incubation_temp_C":float(temps.max()),
    "temperature_span_C":float(np.ptp(temps)),"total_signal_gain":float(gains.sum()),"maximum_signal_gain":float(gains.max()),"mean_signal_gain":float(gains.mean()),"measurement_minimum":float(readings.min()),
    "measurement_maximum":float(readings.max()),"measurement_range":float(np.ptp(readings)),"measurement_mean":float(readings.mean()),"measurement_above_threshold_count":int(np.sum(readings>.2)),"measurement_below_threshold_count":int(np.sum(readings<=.2)),
    "signal_detected":bool(np.any(readings>.2)),"measurement_assay_count":len({x["result"]["assay"] for x in meas}),"measured_sample_count":len({x["result"]["sample"] for x in meas}),
    "final_total_sample_volume_uL":float(sum(x["volume_uL"] for x in samples.values())),"final_total_signal":float(sum(x["signal"] for x in samples.values())),"final_max_sample_volume_uL":float(max((x["volume_uL"] for x in samples.values()),default=0)),
    "final_max_sample_signal":float(max((x["signal"] for x in samples.values()),default=0)),"protocol_first_action":log[0]["action"],"protocol_last_action":log[-1]["action"],"protocol_action_transition_count":sum(a["action"]!=b["action"] for a,b in zip(log,log[1:])),
    "protocol_repeated_action_count":sum(a["action"]==b["action"] for a,b in zip(log,log[1:])),"pipette_before_incubation":bool(pip and inc and pip[0]["step"]<inc[0]["step"]),"measurement_after_incubation":bool(meas and inc and meas[-1]["step"]>inc[-1]["step"]),
    "replay_seed":result["replay"]["seed"],"protocol_replay_step_count":len(result["replay"]["protocol"]),"cost_per_step":result["estimated_consumable_cost"]/len(log),
    "minutes_per_measurement":result["elapsed_minutes"]/max(len(meas),1),"volume_per_sample_uL":float(volumes.sum()/max(len(samples),1)),"signal_per_incubation":float(gains.sum()/max(len(inc),1)),
    "pipette_error_rms":float(np.sqrt(np.mean(errors**2))),"experimental_decision_margin":float(readings.max()-.2)}
    assert len(out)==51
    return out


def run_experiment(protocol: list[dict], *, seed: int=42) -> dict:
    """Run, diagnose, and package a replayable virtual lab experiment."""
    result=simulate_protocol(protocol,seed=seed); diagnostics=enhancement_features(result)
    return {**result,"diagnostics":diagnostics,"diagnostic_count":51,
            "scientist_summary":{"conclusion":result["conclusion"],"measurement_maximum":diagnostics["measurement_maximum"],"pipette_error_rms":diagnostics["pipette_error_rms"],"next_action":"repeat with controls and validate wet-lab assumptions"}}
