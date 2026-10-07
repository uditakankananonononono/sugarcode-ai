from omega.registry import REGISTRY

def test_registry_tracks_actual_rna_scope():
    summary=REGISTRY['rna_decoder'].summary
    assert 'ViennaRNA' in summary and 'functional-effect models Missing' in summary
    assert 'mRNA optimization' not in summary

def test_registry_does_not_call_handset_fate_graph_causal_or_recipe_real():
    summary=REGISTRY['cellfatenet'].summary
    assert 'hand-set GRN simulation' in summary and 'not causal identification' in summary
    assert 'stepwise genetic recipes' not in summary

def test_registry_labels_liquid_models_fitted_only_when_supplied():
    summary=REGISTRY['liquid_biopsy'].summary
    assert 'supplied-label logistic training' in summary and 'not validated cancer diagnosis' in summary

def test_registry_str_no_diagnostic_biomarker_claim():
    summary=REGISTRY['str_scope'].summary
    assert 'anchored sequence tracts' in summary and 'not validated disease prediction' in summary
    assert 'repeat-expansion biomarkers' not in summary
