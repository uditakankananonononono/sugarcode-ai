import numpy as np
import pytest
from sugarcode.modules.neodti_engine import *
def test_multiplex_graph_has_typed_layers():
 g=build_multiplex_graph(); assert g["edge_count"]>g["node_count"] and set(g["layer_counts"])=={"drug","target","pathway","disease"}
def test_real_graph_convolution_is_deterministic_and_normalized():
 g=build_multiplex_graph(); a=graph_neural_embeddings(g,seed=2); b=graph_neural_embeddings(g,seed=2); assert a==b
 assert all(abs(np.linalg.norm(v)-1)<1e-8 for v in a["embeddings"].values())
def test_predictions_have_graph_paths_and_resilience():
 r=predict_interactions("solid tumor"); assert len(r["candidates"])==3 and all(0<=x["therapeutic_resilience_index"]<=1 and x["path_count"]>0 for x in r["candidates"])  # BUG 79: zero-path noise drugs removed
 assert "mechanistic hermetic" in r["model_status"]
def test_exactly_fifty_graph_derived_diagnostics():
 r=analyze_repurposing("solid tumor"); assert len(r["diagnostics"])==50 and len(set(r["diagnostics"]))==50
def test_diseases_change_rankings_and_diagnostics():
 a=analyze_repurposing("solid tumor"); b=analyze_repurposing("arthritis"); assert a["candidates"]!=b["candidates"]
 assert sum(a["diagnostics"][k]!=b["diagnostics"][k] for k in a["diagnostics"])>=10
def test_actionable_validation_plan_and_legacy_api():
 r=analyze_repurposing("aging"); assert len(r["validation_plan"])==4 and repurposing_scan("aging")["candidates"]
def test_invalid_inputs_are_informative():
 with pytest.raises(ValueError,match="dimensions"): graph_neural_embeddings(build_multiplex_graph(),dimensions=1)
 with pytest.raises(KeyError): predict_interactions("not a disease")
