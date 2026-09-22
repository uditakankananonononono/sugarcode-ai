import pytest
from sugarcode.modules.pdx_insight import *
def patient(): return {"mutations":["TP53","KRAS","APC"],"expression":{"A":10,"B":5,"C":2},"copy_number":{"TP53":1,"MYC":4},"methylation":{"P1":.2,"P2":.8}}
def pdx(lost=False,scale=1): return {"mutations":["TP53","KRAS"] if lost else ["TP53","KRAS","APC"],"expression":{"A":10*scale,"B":5/scale,"C":2},"copy_number":{"TP53":1,"MYC":4*scale},"methylation":{"P1":.2*scale,"P2":.8/scale}}
def test_multiomic_fidelity_components_and_lost_drivers():
 r=multiomic_fidelity(patient(),pdx(True),3); assert r["components"]["mutation_retention"]==pytest.approx(2/3) and r["lost_mutations"]==["APC"] and r["crispr_restoration"]
def test_longitudinal_drift_is_case_derived():
 r=longitudinal_drift(patient(),[{"passage":1,"profile":pdx()},{"passage":5,"profile":pdx(True,1.4)}]); assert r["fidelity_slope_per_passage"]<0 and len(r["trajectory"])==2
def test_exactly_fifty_real_diagnostics():
 r=monitor_pdx(patient(),[{"passage":1,"profile":pdx()},{"passage":5,"profile":pdx(True,1.4)}]); assert len(r["diagnostics"])==50 and len(set(r["diagnostics"]))==50
def test_profiles_change_diagnostics_substantially():
 a=monitor_pdx(patient(),[{"passage":1,"profile":pdx()},{"passage":2,"profile":pdx()}]); b=monitor_pdx(patient(),[{"passage":3,"profile":pdx(True,2)},{"passage":9,"profile":pdx(True,3)}]); assert sum(a["diagnostics"][k]!=b["diagnostics"][k] for k in a["diagnostics"])>=30
def test_actionable_report_and_honest_status():
 r=monitor_pdx(patient(),[{"passage":2,"profile":pdx(True)}]); assert r["quality_actions"] and r["restoration_plan"]["targets"]==["APC"] and "no preclinical translation claim" in r["model_status"]
def test_legacy_assessment_remains_available(): assert "model_fidelity_index" in fidelity_assessment(patient(),pdx(),2)
def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="passage"): multiomic_fidelity(patient(),pdx(),-1)
 with pytest.raises(ValueError,match="non-empty"): longitudinal_drift(patient(),[])
 with pytest.raises(ValueError,match="finite"): validate_profile({"expression":{"A":float("nan")}},"bad")
