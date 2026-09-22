from __future__ import annotations
import numpy as _np
_trapz = getattr(_np, "trapezoid", None) or _np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0
import math

EVENTS = {
    "differentiation": [
        (0.0, "baseline proliferative morphology"),
        (0.2, "cell-cycle exit - area increase begins"),
        (0.4, "process outgrowth / lineage marker onset"),
        (0.7, "mature morphology establishment"),
        (1.0, "terminal phenotype stable"),
    ],
    "apoptosis": [
        (0.0, "baseline"), (0.3, "membrane blebbing"), (0.5, "nuclear condensation"),
        (0.7, "cell shrinkage + fragmentation"), (1.0, "apoptotic bodies"),
    ],
    "emt": [
        (0.0, "epithelial cobblestone"), (0.25, "junction dissolution"),
        (0.5, "elongation begins"), (0.75, "mesenchymal spindle morphology"),
        (1.0, "migratory phenotype"),
    ],
}


def simulate_morphology(process: str, duration_h: float = 72.0, frames: int = 25) -> dict:
    """Temporal traces of morphology metrics through a dynamic process."""
    if process not in EVENTS:
        raise KeyError(f"unknown process {process!r}; have {sorted(EVENTS)}")
    events = EVENTS[process]
    traces = {"area": [], "circularity": [], "aspect_ratio": [], "intensity": []}
    timeline = []
    for f in range(frames):
        t = f / (frames - 1)
        hours = round(t * duration_h, 1)
        if process == "differentiation":
            area = 1.0 + 1.5 * t
            circ = 0.9 - 0.5 * t
            aspect = 1.0 + 3.0 * t
            inten = 1.0 + 0.3 * math.sin(4 * math.pi * t)
        elif process == "apoptosis":
            area = 1.0 - 0.7 * t ** 2
            circ = 0.85 + 0.1 * math.sin(10 * t)
            aspect = 1.0 + 0.2 * t
            inten = 1.0 + 0.8 * t
        else:  # emt
            area = 1.0 + 0.4 * t
            circ = 0.9 - 0.6 * t
            aspect = 1.0 + 2.5 * t ** 1.5
            inten = 1.0 - 0.2 * t
        traces["area"].append(round(area, 3))
        traces["circularity"].append(round(circ, 3))
        traces["aspect_ratio"].append(round(aspect, 3))
        traces["intensity"].append(round(inten, 3))
        timeline.append({"t_h": hours, "phase": _phase(events, t)})
    return {
        "process": process, "duration_h": duration_h,
        "event_timeline": [{"t_fraction": e[0], "event": e[1]} for e in events],
        "frames": timeline,
        "traces": traces,
        "morphological_drift": round(traces["area"][-1] - traces["area"][0], 3),
    }


def _phase(events: list, t: float) -> str:
    phase = events[0][1]
    for frac, name in events:
        if t >= frac:
            phase = name
    return phase

# --- specification-complete temporal morphology engine -----------------------
def validate_morphology_state(initial_state: dict) -> dict:
    """Validate physical cell morphology fields and return normalized floats."""
    required=("area_um2","circularity","aspect_ratio","intensity","cell_count")
    if not isinstance(initial_state,dict): raise ValueError("initial_state must be a mapping")
    missing=[x for x in required if x not in initial_state]
    if missing: raise ValueError(f"initial_state missing: {', '.join(missing)}")
    s={k:float(initial_state[k]) for k in required}
    if s["area_um2"]<=0 or s["aspect_ratio"]<1 or s["intensity"]<0 or s["cell_count"]<=0: raise ValueError("area, intensity, cell_count must be positive/non-negative and aspect_ratio >= 1")
    if not 0<s["circularity"]<=1: raise ValueError("circularity must be in (0, 1]")
    return s


def simulate_population_4d(process: str, initial_state: dict, *, duration_h: float=72,
                           sample_interval_h: float=3, stimulus_strength: float=1,
                           heterogeneity: float=.08, seed: int=42) -> dict:
    """Solve population morphology dynamics with an ODE and exact stochastic cells."""
    import numpy as np
    _trapz = getattr(np, "trapezoid", None) or np.trapz  # numpy 1.x/2.x compat: trapz removed in numpy 2.0
    from scipy.integrate import solve_ivp
    if process not in EVENTS: raise ValueError(f"process must be one of {sorted(EVENTS)}")
    s=validate_morphology_state(initial_state)
    if duration_h<=0 or sample_interval_h<=0: raise ValueError("duration_h and sample_interval_h must be positive")
    if stimulus_strength<0 or not 0<=heterogeneity<=1: raise ValueError("stimulus_strength must be non-negative and heterogeneity in [0, 1]")
    targets={"differentiation":(2.5,.4,4,1.1,.002),"apoptosis":(.3,.92,1.2,1.8,-.04),"emt":(1.4,.3,3.5,.8,.008)}[process]
    a0,c0,r0,i0,n0=s.values(); ta,tc,tr,ti,g=targets; scale=max(duration_h/5,1e-6)
    def rhs(_,y):
        a,c,r,inten,n=y; speed=stimulus_strength/scale
        death=max(0,-g); growth=max(0,g)
        return [speed*(a0*ta-a),speed*(tc-c),speed*(tr-r),speed*(i0*ti-inten),(growth*(1-n/(3*n0))-death)*n]
    times=np.arange(0,duration_h+1e-9,sample_interval_h); times=np.unique(np.append(times,duration_h))
    sol=solve_ivp(rhs,(0,duration_h),[a0,c0,r0,i0,n0],t_eval=times,method="LSODA",rtol=1e-9,atol=1e-9)
    if not sol.success: raise RuntimeError(sol.message)
    rng=np.random.default_rng(seed); frames=[]
    for j,t in enumerate(sol.t):
        means=sol.y[:,j]; count=max(1,int(round(means[4]))); sample_n=min(count,500)
        cells=np.column_stack([rng.lognormal(math.log(max(means[0],1e-9))-.5*heterogeneity**2,heterogeneity,sample_n),
          np.clip(rng.normal(means[1],heterogeneity*.2,sample_n),.01,1),np.maximum(1,rng.lognormal(math.log(max(means[2],1))-.5*heterogeneity**2,heterogeneity,sample_n)),
          np.maximum(0,rng.normal(means[3],max(means[3]*heterogeneity,.001),sample_n))])
        frames.append({"time_h":float(t),"phase":_phase(EVENTS[process],float(t/duration_h)),"cell_count":count,
          "area_um2":float(cells[:,0].mean()),"circularity":float(cells[:,1].mean()),"aspect_ratio":float(cells[:,2].mean()),"intensity":float(cells[:,3].mean()),
          "area_cv":float(cells[:,0].std()/cells[:,0].mean()),"shape_cv":float(cells[:,2].std()/cells[:,2].mean())})
    transitions=[]
    for frac,event in EVENTS[process]:
        idx=int(np.argmin(np.abs(sol.t-frac*duration_h))); transitions.append({"time_h":float(frac*duration_h),"event":event,"nearest_frame":idx})
    return {"process":process,"initial_state":s,"duration_h":duration_h,"stimulus_strength":stimulus_strength,"heterogeneity":heterogeneity,"seed":seed,
      "frames":frames,"event_timeline":transitions,"solver":{"method":"LSODA","nfev":sol.nfev,"success":sol.success},
      "model_status":"mechanistic hermetic ODE plus seeded stochastic population; no trained or biological prediction claim"}


def detect_morphology_events(simulation: dict, *, change_threshold: float=.15) -> dict:
    """Detect numerical transitions from morphology traces for scientist review."""
    if change_threshold<=0: raise ValueError("change_threshold must be positive")
    frames=simulation["frames"]; metrics=("area_um2","circularity","aspect_ratio","intensity","cell_count"); events=[]
    for metric in metrics:
        base=float(frames[0][metric]); previous=0
        for f in frames[1:]:
            change=(float(f[metric])-base)/max(abs(base),1e-12)
            band=int(abs(change)/change_threshold)
            if band>previous:
                events.append({"time_h":f["time_h"],"metric":metric,"relative_change":round(change,6),"direction":"increase" if change>0 else "decrease","threshold_multiple":band}); previous=band
    events.sort(key=lambda x:(x["time_h"],x["metric"]))
    return {"events":events,"event_count":len(events),"first_event_hour":events[0]["time_h"] if events else None,"metrics_changed":sorted({x["metric"] for x in events}),"threshold":change_threshold}


def enhancement_features(simulation: dict) -> dict:
    """Compute exactly 52 case-derived temporal morphology diagnostics."""
    import numpy as np
    f=simulation["frames"]; t=np.asarray([x["time_h"] for x in f]); a=np.asarray([x["area_um2"] for x in f]); c=np.asarray([x["circularity"] for x in f]); r=np.asarray([x["aspect_ratio"] for x in f]); i=np.asarray([x["intensity"] for x in f]); n=np.asarray([x["cell_count"] for x in f]); acv=np.asarray([x["area_cv"] for x in f]); scv=np.asarray([x["shape_cv"] for x in f])
    def slope(x): return float(np.polyfit(t,x,1)[0]) if len(t)>1 else 0.
    out={"duration_h":float(t[-1]-t[0]),"frame_count":len(f),"sample_interval_min_h":float(np.diff(t).min()),"sample_interval_max_h":float(np.diff(t).max()),
    "initial_area_um2":float(a[0]),"terminal_area_um2":float(a[-1]),"area_absolute_change_um2":float(a[-1]-a[0]),"area_fold_change":float(a[-1]/a[0]),"area_slope_per_h":slope(a),"area_auc":float(_trapz(a,t)),"area_peak_um2":float(a.max()),"area_peak_hour":float(t[a.argmax()]),
    "initial_circularity":float(c[0]),"terminal_circularity":float(c[-1]),"circularity_absolute_change":float(c[-1]-c[0]),"circularity_slope_per_h":slope(c),"circularity_auc":float(_trapz(c,t)),"circularity_minimum":float(c.min()),"circularity_minimum_hour":float(t[c.argmin()]),
    "initial_aspect_ratio":float(r[0]),"terminal_aspect_ratio":float(r[-1]),"aspect_ratio_absolute_change":float(r[-1]-r[0]),"aspect_ratio_fold_change":float(r[-1]/r[0]),"aspect_ratio_slope_per_h":slope(r),"aspect_ratio_auc":float(_trapz(r,t)),"aspect_ratio_peak":float(r.max()),"aspect_ratio_peak_hour":float(t[r.argmax()]),
    "initial_intensity":float(i[0]),"terminal_intensity":float(i[-1]),"intensity_absolute_change":float(i[-1]-i[0]),"intensity_fold_change":float(i[-1]/max(i[0],1e-12)),"intensity_slope_per_h":slope(i),"intensity_auc":float(_trapz(i,t)),"intensity_peak":float(i.max()),"intensity_peak_hour":float(t[i.argmax()]),
    "initial_cell_count":int(n[0]),"terminal_cell_count":int(n[-1]),"cell_count_absolute_change":int(n[-1]-n[0]),"cell_count_fold_change":float(n[-1]/n[0]),"cell_count_slope_per_h":slope(n),"cell_count_auc":float(_trapz(n,t)),"cell_count_peak":int(n.max()),"cell_count_peak_hour":float(t[n.argmax()]),
    "initial_area_cv":float(acv[0]),"terminal_area_cv":float(acv[-1]),"area_cv_change":float(acv[-1]-acv[0]),"initial_shape_cv":float(scv[0]),"terminal_shape_cv":float(scv[-1]),"shape_cv_change":float(scv[-1]-scv[0]),
    "morphology_drift_norm":float(np.linalg.norm([(a[-1]-a[0])/a[0],c[-1]-c[0],(r[-1]-r[0])/r[0],(i[-1]-i[0])/max(i[0],1e-12)])),"solver_evaluations":simulation["solver"]["nfev"],"event_phase_count":len({x["phase"] for x in f})}
    assert len(out)==52
    return out


def analyze_morphology_4d(process: str, initial_state: dict, **kwargs) -> dict:
    """Run a review-ready temporal cell morphology experiment."""
    sim=simulate_population_4d(process,initial_state,**kwargs); events=detect_morphology_events(sim); diagnostics=enhancement_features(sim)
    return {"simulation":sim,"detected_events":events,"diagnostics":diagnostics,"diagnostic_count":52,
      "scientist_summary":{"process":process,"terminal_cell_count":diagnostics["terminal_cell_count"],"morphology_drift_norm":diagnostics["morphology_drift_norm"],"first_detected_event_h":events["first_event_hour"]},
      "recommended_actions":["compare traces with untreated and vehicle controls","review segmentation quality at detected transitions","validate lineage markers orthogonally"]}
