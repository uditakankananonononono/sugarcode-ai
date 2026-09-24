from __future__ import annotations
import math
import statistics
import time
from omega.registry import REGISTRY

_METRICS: list[dict] = []


def record(module: str, metric: str, value: float, kind: str = "accuracy") -> dict:
    """Record one metric observation (accuracy | efficiency | throughput | latency)."""
    if module not in REGISTRY:
        raise KeyError(f"unknown module {module!r}")
    m = {"module": module, "metric": metric, "value": float(value),
         "kind": kind, "ts": time.time()}
    _METRICS.append(m)
    return m


def recorded_observations(kind: str | None = None) -> list[dict]:
    """Copy of the live record() store, in the input shape performance_dashboard expects."""
    return [dict(m) for m in _METRICS if kind is None or m["kind"] == kind]


def stats(kind: str | None = None) -> dict:
    """Global precision view: per-metric aggregates across the platform."""
    rows = [m for m in _METRICS if kind is None or m["kind"] == kind]
    grouped: dict[str, list[float]] = {}
    for m in rows:
        grouped.setdefault(f"{m['module']}:{m['metric']}:{m['kind']}", []).append(m["value"])
    series = []
    for key, vals in grouped.items():
        module, metric, k = key.split(":", 2)
        series.append({
            "module": module, "metric": metric, "kind": k,
            "n": len(vals), "mean": round(statistics.fmean(vals), 5),
            "stdev": round(statistics.pstdev(vals), 5) if len(vals) > 1 else 0.0,
            "min": round(min(vals), 5), "max": round(max(vals), 5),
        })
    return {"observations": len(rows), "series": series}


def subnetwork_rollup() -> dict:
    """Per-sub-network aggregates: the dashboard's global precision view."""
    base = stats()
    by_sn: dict[str, dict] = {}
    for s in base["series"]:
        sn = REGISTRY[s["module"]].subnetwork
        d = by_sn.setdefault(sn, {"kinds": set(), "metrics": 0, "mean_values": []})
        d["kinds"].add(s["kind"])
        d["metrics"] += 1
        d["mean_values"].append(s["mean"])
    return {
        sn: {"kinds": sorted(d["kinds"]), "metric_series": d["metrics"],
             "mean_of_means": round(sum(d["mean_values"]) / len(d["mean_values"]), 5)
             if d["mean_values"] else 0.0}
        for sn, d in by_sn.items()
    }

VALID_KINDS={"accuracy","efficiency","throughput","latency"}

def validate_observations(observations: list[dict]) -> list[dict]:
    """Validate dashboard input records and normalize timestamps and values."""
    import math
    if not isinstance(observations,list) or not observations: raise ValueError("observations must be a non-empty list")
    out=[]
    for i,row in enumerate(observations):
        if not isinstance(row,dict): raise ValueError(f"observation {i} must be a mapping")
        missing=[x for x in ("module","metric","value","kind","ts") if x not in row]
        if missing: raise ValueError(f"observation {i} missing: {', '.join(missing)}")
        if row["module"] not in REGISTRY: raise ValueError(f"observation {i} unknown module {row['module']!r}")
        if row["kind"] not in VALID_KINDS: raise ValueError(f"observation {i} kind must be one of {sorted(VALID_KINDS)}")
        value=float(row["value"]); ts=float(row["ts"])
        if not math.isfinite(value) or not math.isfinite(ts): raise ValueError(f"observation {i} value and ts must be finite")
        if not str(row["metric"]).strip(): raise ValueError(f"observation {i} metric must be non-empty")
        out.append({**row,"value":value,"ts":ts})
    return out


def performance_dashboard(observations: list[dict], *, now: float | None=None,
                          latency_target_ms: float=1000, throughput_target: float=1,
                          accuracy_target: float=.9, efficiency_target: float=.9) -> dict:
    """Build a transparent performance dashboard with bootstrap uncertainty and drift."""
    import numpy as np
    rows=validate_observations(observations); now=float(time.time() if now is None else now)
    if latency_target_ms<=0 or throughput_target<=0 or accuracy_target<=0 or efficiency_target<=0: raise ValueError("performance targets must be positive")
    targets={"latency":latency_target_ms,"throughput":throughput_target,"accuracy":accuracy_target,"efficiency":efficiency_target}
    groups={}
    for r in rows: groups.setdefault((r["module"],r["metric"],r["kind"]),[]).append(r)
    series=[]
    for (module,metric,kind),data in sorted(groups.items()):
        data=sorted(data,key=lambda x:x["ts"]); v=np.asarray([x["value"] for x in data]); t=np.asarray([x["ts"] for x in data]); n=len(v)
        rng=np.random.default_rng(int(sum(map(ord,module+metric+kind))))
        boot=np.asarray([rng.choice(v,n,replace=True).mean() for _ in range(500)]) if n>1 else np.repeat(v[0],500)
        slope=float(np.polyfit((t-t[0])/3600,v,1)[0]) if n>1 and np.ptp(t)>0 else 0.
        target=targets[kind]
        pass_rate=float(np.mean(v<=target)) if kind=="latency" else float(np.mean(v>=target))
        series.append({"module":module,"subnetwork":REGISTRY[module].subnetwork,"metric":metric,"kind":kind,"n":n,"mean":float(v.mean()),"minimum":float(v.min()),"maximum":float(v.max()),
          "ci95":[float(np.quantile(boot,.025)),float(np.quantile(boot,.975))],"trend_per_hour":slope,"target":target,"pass_rate":pass_rate,"last_value":float(v[-1]),"age_seconds":max(0,now-float(t[-1]))})
    subnet={}
    for name in sorted({x["subnetwork"] for x in series}):
        group=[x for x in series if x["subnetwork"]==name]; subnet[name]={"series_count":len(group),"observation_count":sum(x["n"] for x in group),"mean_pass_rate":sum(x["pass_rate"] for x in group)/len(group),"alert_count":sum(x["pass_rate"]<.8 for x in group)}
    alerts=[]
    for x in series:
        if x["pass_rate"]<.8: alerts.append({"severity":"critical" if x["pass_rate"]<.5 else "warning","module":x["module"],"metric":x["metric"],"kind":x["kind"],"pass_rate":x["pass_rate"],"action":f"review recent {x['kind']} regression"})
    return {"generated_at":now,"observation_count":len(rows),"series":series,"subnetworks":subnet,"alerts":alerts,
      "transparency":{"aggregation":"raw observations -> deterministic grouped metrics","uncertainty":"500-sample seeded bootstrap CI","drift":"least-squares slope per hour","targets":{"latency_ms":latency_target_ms,"throughput":throughput_target,"accuracy":accuracy_target,"efficiency":efficiency_target}},
      "model_status":"deterministic hermetic performance analytics"}


def compare_releases(baseline: list[dict], candidate: list[dict], *, regression_tolerance: float=.05) -> dict:
    """Compare matched release metrics with effect sizes and explicit gates."""
    import numpy as np
    if regression_tolerance<0: raise ValueError("regression_tolerance must be non-negative")
    a=validate_observations(baseline); b=validate_observations(candidate)
    def grouped(rows):
        g={}
        for x in rows: g.setdefault((x["module"],x["metric"],x["kind"]),[]).append(x["value"])
        return g
    ga,gb=grouped(a),grouped(b); common=sorted(set(ga)&set(gb))
    if not common: raise ValueError("baseline and candidate have no matching module/metric/kind series")
    rows=[]
    for key in common:
        av=np.asarray(ga[key]); bv=np.asarray(gb[key]); am,bm=float(av.mean()),float(bv.mean()); lower_better=key[2]=="latency"; improvement=(am-bm)/max(abs(am),1e-12) if lower_better else (bm-am)/max(abs(am),1e-12)
        pooled=math.sqrt((float(av.var())+float(bv.var()))/2) if len(av)>1 or len(bv)>1 else 0.; effect=(bm-am)/pooled if pooled>0 else 0.
        rows.append({"module":key[0],"metric":key[1],"kind":key[2],"baseline_mean":am,"candidate_mean":bm,"relative_improvement":improvement,"standardized_effect":effect,"gate":"fail" if improvement < -regression_tolerance else "pass"})
    return {"comparisons":rows,"pass_count":sum(x["gate"]=="pass" for x in rows),"fail_count":sum(x["gate"]=="fail" for x in rows),"release_gate":"pass" if all(x["gate"]=="pass" for x in rows) else "fail","regression_tolerance":regression_tolerance}


def enhancement_features(dashboard: dict, release_comparison: dict) -> dict:
    """Compute exactly 51 dashboard-derived operational diagnostics."""
    import numpy as np
    s=dashboard["series"]; means=np.asarray([x["mean"] for x in s]); passes=np.asarray([x["pass_rate"] for x in s]); trends=np.asarray([x["trend_per_hour"] for x in s]); ages=np.asarray([x["age_seconds"] for x in s]); widths=np.asarray([x["ci95"][1]-x["ci95"][0] for x in s]); counts=np.asarray([x["n"] for x in s]); comps=release_comparison["comparisons"]; imp=np.asarray([x["relative_improvement"] for x in comps]); effects=np.asarray([x["standardized_effect"] for x in comps])
    kinds={k:[x for x in s if x["kind"]==k] for k in VALID_KINDS}
    out={"observation_count":dashboard["observation_count"],"series_count":len(s),"module_count":len({x["module"] for x in s}),"subnetwork_count":len(dashboard["subnetworks"]),"metric_name_count":len({x["metric"] for x in s}),
    "mean_of_series_means":float(means.mean()),"minimum_series_mean":float(means.min()),"maximum_series_mean":float(means.max()),"series_mean_range":float(np.ptp(means)),"mean_pass_rate":float(passes.mean()),"minimum_pass_rate":float(passes.min()),
    "perfect_pass_series_count":int(np.sum(passes==1)),"failing_pass_series_count":int(np.sum(passes<.8)),"mean_ci_width":float(widths.mean()),"maximum_ci_width":float(widths.max()),"minimum_ci_width":float(widths.min()),
    "positive_trend_count":int(np.sum(trends>0)),"negative_trend_count":int(np.sum(trends<0)),"stable_trend_count":int(np.sum(trends==0)),"maximum_positive_trend":float(max(0,trends.max())),"maximum_negative_trend":float(min(0,trends.min())),
    "freshest_series_age_seconds":float(ages.min()),"stalest_series_age_seconds":float(ages.max()),"mean_series_age_seconds":float(ages.mean()),"minimum_samples_per_series":int(counts.min()),"maximum_samples_per_series":int(counts.max()),
    "mean_samples_per_series":float(counts.mean()),"accuracy_series_count":len(kinds["accuracy"]),"efficiency_series_count":len(kinds["efficiency"]),"throughput_series_count":len(kinds["throughput"]),"latency_series_count":len(kinds["latency"]),
    "alert_count":len(dashboard["alerts"]),"critical_alert_count":sum(x["severity"]=="critical" for x in dashboard["alerts"]),"warning_alert_count":sum(x["severity"]=="warning" for x in dashboard["alerts"]),
    "subnetworks_with_alerts":sum(x["alert_count"]>0 for x in dashboard["subnetworks"].values()),"maximum_subnetwork_alerts":max((x["alert_count"] for x in dashboard["subnetworks"].values()),default=0),
    "comparison_count":len(comps),"release_pass_count":release_comparison["pass_count"],"release_fail_count":release_comparison["fail_count"],"relative_improvement_mean":float(imp.mean()),"relative_improvement_minimum":float(imp.min()),
    "relative_improvement_maximum":float(imp.max()),"improved_comparison_count":int(np.sum(imp>0)),"regressed_comparison_count":int(np.sum(imp<0)),"standardized_effect_mean":float(effects.mean()),"maximum_absolute_effect":float(np.max(np.abs(effects))),
    "regression_tolerance":release_comparison["regression_tolerance"],"release_gate_pass":release_comparison["release_gate"]=="pass","observations_per_module":dashboard["observation_count"]/len({x["module"] for x in s}),
    "alert_fraction":len(dashboard["alerts"])/len(s),"dashboard_reliability_score":float(passes.mean()*(1-len(dashboard["alerts"])/len(s)))}
    assert len(out)==51
    return out


def build_omega_report(observations: list[dict], baseline: list[dict], *, now: float | None=None) -> dict:
    """Build an auditable platform report and release decision."""
    dash=performance_dashboard(observations,now=now); comparison=compare_releases(baseline,observations); diagnostics=enhancement_features(dash,comparison)
    return {"dashboard":dash,"release_comparison":comparison,"diagnostics":diagnostics,"diagnostic_count":51,
      "operational_actions":[x["action"] for x in dash["alerts"]] or ["no active threshold regressions; continue routine monitoring"],
      "release_decision":comparison["release_gate"],"model_status":"deterministic hermetic transparent performance analytics"}
