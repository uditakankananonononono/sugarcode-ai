import numpy as np
from sugarcode.modules.cellfatenet import *
SRC={"OCT4":1,"SOX2":1,"NANOG":1}; TAR={"ASCL1":1,"NEUROD1":1,"MYT1L":1,"TUBB3":1,"MAP2":1}
def test_grn_signed_edges_and_chromatin_occupancy():
 n,w=grn_matrix(); assert (w>0).any() and (w<0).any(); r=chromatin_binding([1,.1],[0,.9],1); assert r["occupancy"][0]>r["occupancy"][1]
def test_simulation_is_dynamic_and_epigenetically_gated():
 a=simulate_fate(SRC,hours=2); b=simulate_fate(SRC,hours=2,methylation={n:1 for n in a["nodes"]}); assert a["final_state"]!=b["final_state"]
def test_attractors_have_normalized_basins():
 r=identify_attractors(starts=8); assert np.isclose(sum(x["basin_fraction"] for x in r["attractors"]),1)
def test_graph_message_passing_is_honestly_untrained():
 r=graph_message_passing(SRC); assert len(r["layers"])==4 and "untrained" in r["method"]
def test_optimal_control_and_stochastic_validation_execute():
 c=optimal_reprogramming(SRC,TAR,hours=2,max_factors=2); v=stochastic_validate(SRC,TAR,c["interventions"],replicates=4); assert len(c["interventions"])<=2 and 0<=v["success_probability"]<=1
def test_end_to_end_50_computed_diagnostics_disclaimer_separate():
 r=design_fate_transition(SRC,TAR,hours=2); assert len(r["diagnostics"])>=50 and r["enhancement_feature_count"]==len(r["diagnostics"]); assert "model_status" not in r["diagnostics"] and "not clinically validated" in r["model_status"]
