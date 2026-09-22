import numpy as np
import pytest
from sugarcode.modules.biosimvr import *

def protocol(): return [{"action":"pipette","sample":"A","volume_uL":50,"cv":.01},{"action":"incubate","sample":"A","minutes":240,"temp_C":37},{"action":"measure","sample":"A","assay":"fluorescence"}]

def test_virtual_protocol_is_deterministic_replayable_and_actionable():
 a=simulate_protocol(protocol(),seed=3); b=simulate_protocol(protocol(),seed=3)
 assert a==b and a["execution_log"][-1]["result"]["reading"]>0
 assert a["replay"]["protocol"]==protocol() and "mechanistic hermetic" in a["model_status"]

def test_docking_uses_real_global_optimizer():
 lig=[[0,0,0],[1,0,0],[0,1,0]]; pocket=[[4,4,4],[5,4,4],[4,5,4],[4,4,5]]
 r=molecular_docking_experiment(lig,pocket,steps=10,seed=2)
 assert r["evaluations"]>20 and len(r["optimized_pose_xyz"])==3 and r["contacts_under_4A"]>0

def test_crispr_experiment_enumerates_and_ranks_real_guides():
 r=crispr_design_experiment("A"*10+"GCGCGCGCGCGCGCGCGCGCAGG"+"T"*10)
 assert r["candidate_count"]>=1 and r["recommended"]["pam"].endswith("GG")
 assert 0<=r["recommended"]["score"]<=1 and r["conclusion"]

def test_exactly_fifty_one_result_derived_diagnostics_vary():
 a=run_experiment(protocol(),seed=1); b=run_experiment([{"action":"pipette","sample":"B","volume_uL":100,"cv":.08},{"action":"incubate","sample":"B","minutes":30,"temp_C":25},{"action":"measure","sample":"B"}],seed=7)
 assert len(a["diagnostics"])==51 and len(set(a["diagnostics"]))==51
 assert sum(a["diagnostics"][k]!=b["diagnostics"][k] for k in a["diagnostics"])>=20

def test_end_to_end_has_scientist_summary():
 r=run_experiment(protocol(),seed=5)
 assert r["diagnostic_count"]==51 and r["scientist_summary"]["next_action"]

def test_legacy_scene_and_session_remain_available():
 lab=default_lab(); assert lab.move_to("p1000","plate_96")>0
 assert run_session("crispr_transfection")["observations"]

def test_invalid_inputs_are_informative():
 with pytest.raises(ValueError,match="non-empty"): simulate_protocol([])
 with pytest.raises(ValueError,match="unknown action"): simulate_protocol([{"action":"teleport"}])
 with pytest.raises(ValueError,match="A/C/G/T"): crispr_design_experiment("AXTG")
