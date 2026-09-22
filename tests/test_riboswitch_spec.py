import pytest
from sugarcode.modules.riboswitch import *
def test_exact_nussinov_fold_is_valid_and_deterministic():
 a=nussinov_fold("GGGAAACCC"); b=nussinov_fold("GGGAAACCC"); assert a==b and a["pair_count"]>=2 and len(a["dot_bracket"])==9 and a["algorithm"].startswith("exact")
def test_sequence_search_has_live_alternatives():
 r=optimize_switch("theophylline",candidates=12); assert len(r["ranking"])==12 and r["ranking"][0]["score"]>r["ranking"][1]["score"] and len({x["stem"] for x in r["ranking"]})==12
def test_response_curve_has_kd_half_occupancy_and_modes():
 a=response_curve(1,mode="on",concentrations=[0,1,10]); b=response_curve(1,mode="off",concentrations=[0,1,10]); assert a["curve"][1]["occupancy"]==pytest.approx(.5) and a["curve"][0]["signal"]<a["curve"][-1]["signal"] and b["curve"][0]["signal"]>b["curve"][-1]["signal"]
def test_exactly_fifty_case_derived_diagnostics():
 r=design_sensor("theophylline",candidates=12); assert len(r["diagnostics"])==50 and len(set(r["diagnostics"]))==50
def test_end_to_end_is_actionable_and_honest():
 r=design_sensor("SAM",mode="off",candidates=8); assert r["diagnostic_count"]==50 and r["structure"]["dot_bracket"] and len(r["validation"])==4 and "no sensor performance claim" in r["response"]["model_status"]
def test_legacy_designer_remains_available(): assert design_riboswitch("adenine")["sequence"]
def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="RNA sequence"): validate_rna("AXTG")
 with pytest.raises(ValueError,match="ligand"): optimize_switch("fake")
 with pytest.raises(ValueError,match="kd_uM"): response_curve(0)
