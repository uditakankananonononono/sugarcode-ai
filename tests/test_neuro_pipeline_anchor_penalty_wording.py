"""The continual-learning note describes the weight-anchor penalty and keeps the ewc_lambda key."""
import numpy as np

from sugarcode.modules.neuro_pipeline.core import MLP, continual_update, train


def test_train_note_says_weight_anchor_no_fisher():
    note = train(epochs=5, seed=0)["plasticity_note"]
    assert "STDP" in note and "continual_update" in note
    assert "weight-anchor penalty" in note and "no Fisher term" in note
    assert "EWC-style penalty hook" not in note


def test_continual_update_doc_and_key():
    doc = continual_update.__doc__ or ""
    assert "weight-anchor penalty" in doc and "no Fisher term" in doc
    out = continual_update(MLP(2, 3, 1), np.array([[0, 0], [1, 1]], float), np.array([[0], [1]], float), epochs=2)
    assert "ewc_lambda" in out
