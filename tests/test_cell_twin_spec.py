import pytest
from sugarcode.modules.cell_twin import *
def omics(): return {"mutations":[{"gene":"KRAS","driver_score":.9}],"expression":{"MKI67":80,"PCNA":50,"BAX":20,"BCL2":40,"BRCA1":30,"KRAS":60},"proteomics":{"AKT1":20},"metabolomics":{"lactate":5}}
def test_reproducible_multiomic_twin_and_honest_status():
 a=build_mechanistic_twin(omics()); b=build_mechanistic_twin(omics()); assert a==b and a["twin_id"].startswith("celltwin-") and "no trained" in a["model_status"]
def test_real_ode_drug_response_is_dose_sensitive():
 t=build_mechanistic_twin(omics()); a=simulate_drug_response(t,"cisplatin",.1,hours=24); b=simulate_drug_response(t,"cisplatin",10,hours=24); assert a["solver"]["success"] and b["terminal_viability"]<a["terminal_viability"]
def test_combination_screen_has_live_bliss_alternatives():
 r=combination_screen(build_mechanistic_twin(omics()),["cisplatin","olaparib","venetoclax"],[1,2,3]); assert len(r["combinations"])==3 and r["recommended"]["bliss_excess"]>0
def test_exactly_fifty_case_derived_diagnostics():
 r=run_virtual_trial(omics(),["cisplatin","olaparib","venetoclax"],[1,2,3]); assert len(r["diagnostics"])==50 and len(set(r["diagnostics"]))==50
def test_actionable_trial_output():
 r=run_virtual_trial(omics(),["cisplatin","olaparib"],[1,2]); assert r["diagnostic_count"]==50 and len(r["validation_plan"])==4 and r["screen"]["recommended"]
def test_legacy_api_remains_available():
 t=create_twin(omics()); assert run_drug_trial(t,["cisplatin","olaparib"])["recommended"]
def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="expression"): validate_patient_omics({})
 with pytest.raises(ValueError,match="unknown drug"): simulate_drug_response(build_mechanistic_twin(omics()),"fake",1)
 with pytest.raises(ValueError,match="matching dose"): combination_screen(build_mechanistic_twin(omics()),["cisplatin","olaparib"],[1])
