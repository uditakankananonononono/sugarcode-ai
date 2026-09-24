import pytest
from sugarcode.modules.omega_stats import *

def rows(mult=1):
 return [{"module":"crispr_opt","metric":"precision","kind":"accuracy","value":v*mult,"ts":1000+i*3600} for i,v in enumerate([.8,.85,.9])]+[{"module":"docking_studio","metric":"runtime","kind":"latency","value":v*mult,"ts":1000+i*3600} for i,v in enumerate([900,1100,700])]+[{"module":"virtual_cell","metric":"jobs","kind":"throughput","value":v*mult,"ts":1000+i*3600} for i,v in enumerate([2,3,4])]

def test_dashboard_has_bootstrap_uncertainty_drift_targets_and_subnetworks():
 r=performance_dashboard(rows(),now=20000)
 assert r["observation_count"]==9 and len(r["series"])==3 and len(r["subnetworks"])==3
 assert all(len(x["ci95"])==2 for x in r["series"]) and r["transparency"]["uncertainty"]

def test_latency_direction_is_lower_better_for_release_gate():
 base=rows(); cand=rows();
 for x in cand:
  if x["kind"]=="latency": x["value"]*=.8
 r=compare_releases(base,cand); latency=next(x for x in r["comparisons"] if x["kind"]=="latency")
 assert latency["relative_improvement"]>0 and latency["gate"]=="pass"

def test_regression_fails_explicit_release_gate():
 r=compare_releases(rows(),rows(.5)); assert r["release_gate"]=="fail" and r["fail_count"]>0

def test_exactly_fifty_one_dashboard_derived_diagnostics():
 report=build_omega_report(rows(),rows(.95),now=20000); f=report["diagnostics"]
 assert len(f)==51 and len(set(f))==51 and f["observation_count"]==9

def test_report_is_actionable_and_transparent():
 r=build_omega_report(rows(),rows(.95),now=20000)
 assert r["diagnostic_count"]==51 and r["operational_actions"] and r["release_decision"] in {"pass","fail"}
 assert "transparent" in r["model_status"]

def test_legacy_metric_store_remains_available():
 from sugarcode.modules.omega_stats import core
 before=list(core._METRICS)
 try:
  m=record("crispr_opt","unit_test_accuracy",.9); assert m["value"]==.9
  assert stats()["observations"]>=1 and "genome-editing" in subnetwork_rollup()
 finally:
  core._METRICS[:]=before

def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="non-empty"): validate_observations([])
 with pytest.raises(ValueError,match="kind"): validate_observations([{**rows()[0],"kind":"unknown"}])
 with pytest.raises(ValueError,match="targets"): performance_dashboard(rows(),latency_target_ms=0)


def test_audit_accuracy_target_default_and_health_feed():
    import time as _t
    from sugarcode.modules.omega_stats import performance_dashboard, recorded_observations
    from omega.health import compute_flux
    now = _t.time()
    obs = [{"module": "crispr_opt", "metric": "precision", "value": v, "kind": "accuracy", "ts": now - i}
           for i, v in enumerate([.95, .96, .97])]
    assert performance_dashboard(obs, now=now)["alerts"] == []
    bad = [dict(o, value=.5) for o in obs]
    assert performance_dashboard(bad, now=now)["alerts"][0]["severity"] == "critical"
    before = len(recorded_observations("latency"))
    compute_flux()
    assert len(recorded_observations("latency")) > before
